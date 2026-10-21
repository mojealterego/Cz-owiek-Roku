"""Strict terrain elevation ETL: source GeoTIFF → local metre-aligned Godot tiles.

This tool NEVER creates heights without a valid source pixel. nodata remains null.
The exported vertical datum is copied from user-confirmed source metadata; it is
NOT reprojected by pyproj and it is NOT implicitly aligned to OSM road geometry.
All output has QA status until horizontal/vertical/historical acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path

import rasterio
from pyproj import CRS, Transformer

SIZE_M = 256
SPACING_M = {8, 16, 32, 64}
MAX_TILES = 64
MAX_SOURCE_BYTES = 1024 * 1024 * 1024
SUPPORTED_SOURCE_CRS = {"EPSG:2180", "EPSG:2177", "EPSG:2178", "EPSG:2179",
                        "EPSG:5514", "EPSG:4326"}
IDENT = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,79}$")
DATUM = re.compile(r"^[A-Za-z0-9_.:+/-]{3,100}$")


class TerrainError(ValueError):
    pass


def local_crs(lon: float, lat: float) -> CRS:
    if not (-180.0 <= lon <= 180.0 and -90.0 <= lat <= 90.0
            and math.isfinite(lon) and math.isfinite(lat)):
        raise TerrainError("Invalid WGS84 anchor")
    return CRS.from_proj4(
        f"+proj=aeqd +lat_0={lat:.12f} +lon_0={lon:.12f} +datum=WGS84 +units=m +no_defs"
    )


def hash_source(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(4 * 1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def export_geotiff(
    input_path: Path,
    output_dir: Path,
    *,
    city_id: str,
    source_id: str,
    source_url: str,
    license_id: str,
    vertical_datum: str,
    source_epoch: str,
    anchor_lon: float = 18.6332106,
    anchor_lat: float = 49.74816,
    west: int = -1,
    east: int = 0,
    south: int = -1,
    north: int = 0,
    spacing_m: int = 32,
    internal_preview: bool = False,
    rights_approved: bool = False,
    zero_is_unverified_nodata: bool = False,
) -> dict:
    for label in (city_id, source_id):
        if not isinstance(label, str) or not IDENT.fullmatch(label):
            raise TerrainError("Invalid city or source ID")
    if not isinstance(source_url, str) or not source_url.startswith("https://"):
        raise TerrainError("Source URL must be HTTPS")
    if not isinstance(license_id, str) or not license_id.strip():
        raise TerrainError("Source reuse terms must be identified")
    if not isinstance(vertical_datum, str) or not DATUM.fullmatch(vertical_datum):
        raise TerrainError("Explicit vertical datum required, e.g. PL-EVRF2007-NH or CZ-BPV")
    if vertical_datum.startswith("TEST_") and not internal_preview:
        raise TerrainError("Synthetic test datum cannot be used for release")
    if not isinstance(source_epoch, str) or (source_epoch != "UNKNOWN" and
            not re.fullmatch(r"20[0-9]{2}", source_epoch)):
        raise TerrainError("Source reference epoch YYYY or explicit UNKNOWN required")
    if not rights_approved and not internal_preview:
        raise TerrainError("Source rights must be approved or export limited to internal preview")
    if not isinstance(spacing_m, int) or spacing_m not in SPACING_M:
        raise TerrainError("Grid spacing must be an approved 256m divisor")
    if not all(type(v) is int for v in (west, east, south, north)):
        raise TerrainError("Tile indices must be integers")
    if west > east or south > north or (east - west + 1) * (north - south + 1) > MAX_TILES:
        raise TerrainError("Invalid/broad tile bounds")
    if not input_path.is_file() or not (0 < input_path.stat().st_size <= MAX_SOURCE_BYTES):
        raise TerrainError("Missing or excessive terrain source")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise TerrainError("Refusing to overwrite terrain output")
    frame = local_crs(anchor_lon, anchor_lat)
    sha = hash_source(input_path)
    tiles: list[tuple[str, dict]] = []
    count_valid = 0
    masked_unverified_zeros = 0
    with rasterio.open(input_path) as source:
        if source.driver != "GTiff" or source.count != 1 or source.crs is None:
            raise TerrainError("Input must be single-band, georeferenced GeoTIFF")
        source_code = source.crs.to_string()
        if source_code not in SUPPORTED_SOURCE_CRS:
            raise TerrainError(f"Source horizontal CRS not explicitly supported: {source_code}")
        if source.width < 2 or source.height < 2:
            raise TerrainError("Terrain raster must have non-degenerate dimensions")
        if source.scales[0] != 1.0 or source.offsets[0] != 0.0:
            raise TerrainError("Preapply raster elevation scale and offset before import")
        transformer = Transformer.from_crs(frame, CRS.from_user_input(source_code),
                                           always_xy=True)
        cells = SIZE_M // spacing_m
        npoints = cells + 1
        for i in range(west, east + 1):
            for j in range(south, north + 1):
                sample_xy = []
                for y in range(npoints):
                    for x in range(npoints):
                        east_m = i * SIZE_M + x * spacing_m
                        north_m = j * SIZE_M + y * spacing_m
                        projected = transformer.transform(east_m, north_m)
                        if not all(math.isfinite(c) for c in projected):
                            raise TerrainError("Invalid local → source CRS transform")
                        sample_xy.append(projected)
                heights: list[float | None] = []
                for sample in source.sample(sample_xy, indexes=1, masked=True):
                    h = sample[0]
                    if bool(getattr(h, "mask", False)):
                        heights.append(None)
                        continue
                    value = float(h)
                    if zero_is_unverified_nodata and value == 0.0:
                        # DMR5G Cieszyn raw ImageServer sometimes writes 0 for
                        # uncovered areas without a TIFF nodata mask. Unknown
                        # area must stay UNKNOWN, never become a flat 0m valley.
                        heights.append(None)
                        masked_unverified_zeros += 1
                        continue
                    if not math.isfinite(value) or abs(value) > 12000:
                        heights.append(None)
                    else:
                        heights.append(round(value, 4))
                        count_valid += 1
                tile = {
                    "schema_version": 1, "type": "GEOREFERENCED_TERRAIN_QA_TILE",
                    "city_id": city_id, "tile_id": f"E{i:+07d}_N{j:+07d}",
                    "origin_east_m": i * SIZE_M, "origin_north_m": j * SIZE_M,
                    "tile_size_m": SIZE_M, "spacing_m": spacing_m,
                    "grid_width": npoints, "grid_height": npoints,
                    "heights_m": heights, "nodata_count": heights.count(None),
                    "vertical_datum": vertical_datum,
                    "terrain_alignment": "UNREGISTERED_TO_BUILDINGS",
                }
                tiles.append((tile["tile_id"] + ".json", tile))
    if count_valid == 0:
        raise TerrainError("Source covers no terrain samples in the requested area")
    summary = {
        "schema_version": 1, "type": "WORLD_SOURCE_TERRAIN_QA",
        "status": "GEOTIFF_IMPORTED_NOT_HISTORICALLY_VALIDATED",
        "city_id": city_id, "source_id": source_id, "source_url": source_url,
        "source_sha256": sha, "source_epoch": source_epoch,
        "source_crs": source_code, "anchor_wgs84": {"lon": anchor_lon, "lat": anchor_lat},
        "vertical_datum": vertical_datum, "vertical_conversion_applied": False,
        "vertical_registration_to_game": "NOT_VERIFIED",
        "rights_review_status": ("APPROVED_BY_OPERATOR" if rights_approved
                                 else "REVIEW_PENDING_INTERNAL_ONLY"),
        "license_id": license_id, "spacing_m": spacing_m,
        "tile_size_m": SIZE_M, "tile_count": len(tiles),
        "valid_sample_count": count_valid,
        "nodata_sample_count": sum(t["nodata_count"] for _, t in tiles),
        "suspect_zero_value_masked_count": masked_unverified_zeros,
        "zero_value_policy": ("MASKED_AS_UNVERIFIED_VOID_FOR_THIS_AREA"
                              if zero_is_unverified_nodata else "SOURCE_PRESERVED"),
        "historical_facades_validated": False,
        "terrain_source_coverage_complete": False,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    for filename, tile in tiles:
        (output_dir / filename).write_text(json.dumps(tile, ensure_ascii=False,
            sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    (output_dir / "manifest.json").write_text(json.dumps(summary, indent=2,
        ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    for name in ("city-id", "source-id", "source-url", "license-id", "vertical-datum",
                 "source-epoch"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--anchor-lon", type=float, default=18.6332106)
    parser.add_argument("--anchor-lat", type=float, default=49.74816)
    parser.add_argument("--west", type=int, default=-1)
    parser.add_argument("--east", type=int, default=0)
    parser.add_argument("--south", type=int, default=-1)
    parser.add_argument("--north", type=int, default=0)
    parser.add_argument("--spacing-m", type=int, default=32)
    parser.add_argument("--internal-preview", action="store_true")
    parser.add_argument("--rights-approved", action="store_true")
    parser.add_argument("--zero-is-unverified-nodata", action="store_true")
    args = parser.parse_args()
    kw = vars(args)
    kw["input_path"] = kw.pop("input")
    kw["output_dir"] = kw.pop("output_dir")
    summary = export_geotiff(**kw)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
