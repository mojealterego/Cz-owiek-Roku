"""Source-preserving, metrically accurate GIS → mobile tile JSON converter.

Imports actual user-supplied GeoJSON; does not scrape map tiles or invent city geometry.
Projection: source EPSG → common WGS84-anchored local azimuthal equidistant (metres).
Tile geometry is clipped without simplification; unknown elevation remains UNKNOWN.
Run: python -m geodata.geoetl --help
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from pyproj import CRS, Transformer, __version__ as proj_version
from shapely.geometry import box, mapping, shape
from shapely.ops import transform

SIZE_M = 256
MAX_INPUT_SIZE = 32 * 1024 * 1024
MAX_FEATURES = 20_000
MAX_TILES_PER_FEATURE = 4096
MAX_RADIUS_M = 30_000.0
SAFE_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,79}$")
GEOMETRIES = {"Point", "LineString", "MultiLineString", "Polygon", "MultiPolygon"}
VALID_CRS = {"EPSG:4326", "EPSG:2180", "EPSG:5514"}
PUBLIC_LICENSES = {"ODbL-1.0", "CC0-1.0"}
VALID_YEARS = {"2023", "2024", "2025", "2026"}


class GeoETLError(ValueError):
    pass


def grid_index(east_m: float, north_m: float) -> tuple[int, int]:
    if not (math.isfinite(east_m) and math.isfinite(north_m)):
        raise GeoETLError("Non-finite metric coordinate")
    return math.floor(east_m / SIZE_M), math.floor(north_m / SIZE_M)


def tile_id(i: int, j: int) -> str:
    return f"E{i:+07d}_N{j:+07d}"


def metric_transformer(source_crs: str, anchor_lon: float, anchor_lat: float) -> Transformer:
    if source_crs not in VALID_CRS:
        raise GeoETLError(f"Unsupported source CRS: {source_crs}")
    if not (math.isfinite(anchor_lon) and math.isfinite(anchor_lat)):
        raise GeoETLError("Anchor must be finite")
    if not (-180.0 <= anchor_lon <= 180.0 and -90.0 <= anchor_lat <= 90.0):
        raise GeoETLError("Invalid geographic anchor")
    local = CRS.from_proj4(
        f"+proj=aeqd +lat_0={anchor_lat:.12f} +lon_0={anchor_lon:.12f} "
        "+datum=WGS84 +units=m +no_defs"
    )
    return Transformer.from_crs(CRS.from_user_input(source_crs), local, always_xy=True)


def _sanitize_feature(feature: dict[str, Any]) -> tuple[str, str, str, Any]:
    if not isinstance(feature, dict) or feature.get("type") != "Feature":
        raise GeoETLError("Expected GeoJSON Feature")
    identity = feature.get("id")
    if not isinstance(identity, str) or not SAFE_ID.fullmatch(identity):
        raise GeoETLError("Every feature must have a stable safe ASCII ID")
    properties = feature.get("properties")
    if not isinstance(properties, dict):
        raise GeoETLError(f"Missing properties for {identity}")
    kind = properties.get("kind")
    if kind not in ("landmark", "road", "building"):
        raise GeoETLError(f"Unsupported feature category: {identity}")
    name = properties.get("name", "")
    if not isinstance(name, str) or len(name) > 160:
        raise GeoETLError(f"Invalid name for {identity}")
    raw = feature.get("geometry")
    if not isinstance(raw, dict) or raw.get("type") not in GEOMETRIES:
        raise GeoETLError(f"Unsupported GeoJSON geometry: {identity}")
    geometry = shape(raw)
    if geometry.is_empty or not geometry.is_valid or geometry.has_z:
        raise GeoETLError(f"Empty, invalid or 3D geometry: {identity}")
    expected = (
        ("Point",) if kind == "landmark"
        else (("LineString", "MultiLineString") if kind == "road" else ("Polygon", "MultiPolygon"))
    )
    if geometry.geom_type not in expected:
        raise GeoETLError(f"Kind and geometry disagree: {identity}")
    attributes: dict[str, Any] = {}
    if kind == "building":
        explicit_height = properties.get("height_m")
        height_source = properties.get("height_source")
        height_status = properties.get("height_status")
        if explicit_height is not None:
            if (not isinstance(explicit_height, (int, float))
                    or isinstance(explicit_height, bool)
                    or not math.isfinite(explicit_height)
                    or not (0.5 <= float(explicit_height) <= 300.0)
                    or height_source != "OSM_HEIGHT_TAG"
                    or height_status != "OSM_REPORTED_UNVERIFIED"):
                raise GeoETLError(f"Unverified or invalid building height: {identity}")
            attributes["height_m"] = float(explicit_height)
            attributes["height_source"] = height_source
            attributes["height_status"] = height_status
        elif height_source is not None or height_status is not None:
            raise GeoETLError(f"Orphaned height provenance: {identity}")
        floors = properties.get("building_levels")
        if floors is not None:
            if (type(floors) is not int or not (1 <= floors <= 99)
                    or properties.get("levels_status") != "OSM_LEVEL_COUNT_ONLY_NOT_HEIGHT"):
                raise GeoETLError(f"Invalid floor count or provenance: {identity}")
            attributes["building_levels"] = floors
            attributes["levels_status"] = "OSM_LEVEL_COUNT_ONLY_NOT_HEIGHT"
    return identity, kind, name, geometry, attributes


def _coordinate_pairs(geometry: Any) -> Any:
    """Shapely mapping contains tuples, all coordinates are relative to tile SW origin."""
    return mapping(geometry)["coordinates"]


def _clip_projected_geometry(
    feature_id: str, kind: str, name: str, geom: Any, attributes: dict[str, Any]
) -> list[tuple[tuple[int, int], dict[str, Any]]]:
    min_e, min_n, max_e, max_n = geom.bounds
    if not all(math.isfinite(v) for v in (min_e, min_n, max_e, max_n)):
        raise GeoETLError("Non-finite projection")
    if max(abs(min_e), abs(min_n), abs(max_e), abs(max_n)) > MAX_RADIUS_M:
        raise GeoETLError(f"Out of city radius: {feature_id}")
    a, b = grid_index(min_e, min_n)
    c, d = grid_index(max_e, max_n)
    tiles = (c - a + 1) * (d - b + 1)
    if tiles > MAX_TILES_PER_FEATURE:
        raise GeoETLError(f"Unbounded tile coverage: {feature_id}")
    if kind == "landmark":
        a, b = grid_index(geom.x, geom.y)
        c, d = a, b
    result: list[tuple[tuple[int, int], dict[str, Any]]] = []
    for i in range(a, c + 1):
        for j in range(b, d + 1):
            tile = box(i * SIZE_M, j * SIZE_M, (i + 1) * SIZE_M, (j + 1) * SIZE_M)
            piece = geom.intersection(tile)
            if piece.is_empty:
                continue
            if kind == "road":
                if piece.geom_type not in ("LineString", "MultiLineString"):
                    continue
                if piece.length <= 1e-8:
                    continue
            if kind == "building":
                if piece.geom_type not in ("Polygon", "MultiPolygon"):
                    continue
                if piece.area <= 1e-8:
                    continue
            local = transform(lambda x, y, z=None: (x - i * SIZE_M, y - j * SIZE_M), piece)
            result.append(((i, j), {
                "id": feature_id, "kind": kind, "name": name,
                "geometry_type": local.geom_type,
                "coordinates": _coordinate_pairs(local),
                "elevation_status": "UNKNOWN_NO_TERRAIN",
                **attributes,
            }))
    return result


def build(
    input_file: Path,
    output_dir: Path,
    *,
    city_id: str,
    source_crs: str,
    anchor_lon: float,
    anchor_lat: float,
    source_id: str,
    source_url: str,
    license_id: str,
    year: str,
    internal_preview: bool = False,
) -> dict[str, Any]:
    if not SAFE_ID.fullmatch(city_id) or not SAFE_ID.fullmatch(source_id):
        raise GeoETLError("Unsafe city/source identifier")
    if year not in VALID_YEARS:
        raise GeoETLError("Only 2023–2026 source snapshot years permitted")
    if not source_url.startswith(("https://", "http://")) or len(source_url) > 2048:
        raise GeoETLError("Provenance URL missing/invalid")
    if not isinstance(license_id, str) or len(license_id) > 80:
        raise GeoETLError("License identifier missing/invalid")
    public_allowed = license_id in PUBLIC_LICENSES
    if not public_allowed and not internal_preview:
        raise GeoETLError("Source license unresolved: use --internal-preview for non-release data")
    if not input_file.is_file() or input_file.stat().st_size > MAX_INPUT_SIZE:
        raise GeoETLError("Source missing or exceeds 32 MiB")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise GeoETLError("Output folder must be empty; refusing overwrite")
    source_bytes = input_file.read_bytes()
    try:
        raw = json.loads(source_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GeoETLError("Invalid UTF-8 GeoJSON") from exc
    if not isinstance(raw, dict) or raw.get("type") != "FeatureCollection":
        raise GeoETLError("Input must be a GeoJSON FeatureCollection")
    features = raw.get("features")
    if not isinstance(features, list) or len(features) > MAX_FEATURES:
        raise GeoETLError("Invalid or excessive number of features")
    t = metric_transformer(source_crs, anchor_lon, anchor_lat)
    tiles: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    seen: set[str] = set()
    height_sourced_ids: set[str] = set()
    levels_only_ids: set[str] = set()
    for f in features:
        uid, kind, name, g, attributes = _sanitize_feature(f)
        if uid in seen:
            raise GeoETLError(f"Duplicate feature ID: {uid}")
        seen.add(uid)
        if "height_m" in attributes:
            height_sourced_ids.add(uid)
        elif "building_levels" in attributes:
            levels_only_ids.add(uid)
        geo = transform(t.transform, g)
        if not geo.is_valid:
            raise GeoETLError(f"Invalid geometry after projection: {uid}")
        for tile, piece in _clip_projected_geometry(uid, kind, name, geo, attributes):
            tiles[tile].append(piece)
    summary = {
        "schema_version": 1, "type": "WORLD_METRIC_TILES",
        "build_status": ("CURRENT_BASEMAP_NOT_HISTORICALLY_VERIFIED" if year == "2026"
                         else "PREVIEW_ONLY_NOT_HISTORICALLY_VERIFIED"),
        "city_id": city_id, "historical_year": year,
        "tile_size_m": SIZE_M,
        "anchor_wgs84": {"lon": anchor_lon, "lat": anchor_lat},
        "projection": "LOCAL_WGS84_AEQD",
        "source_crs": source_crs, "proj_version": proj_version,
        "source": {"id": source_id, "url": source_url, "license": license_id,
                   "sha256": hashlib.sha256(source_bytes).hexdigest()},
        "redistribution_allowed": public_allowed,
        "source_features": len(features), "tile_count": len(tiles),
        "buildings_height_status": "UNKNOWN",
        "terrain_status": "MISSING",
        "facades_historical_status": "NOT_VERIFIED",
        "explicit_osm_height_count": len(height_sourced_ids),
        "levels_without_measured_height_count": len(levels_only_ids),
        "height_geometry_status": "PREVIEW_RELATIVE_TO_UNKNOWN_GROUND",
    }
    # All validation completes before any filesystem mutation.
    output_dir.mkdir(parents=True, exist_ok=True)
    for i, j in sorted(tiles):
        payload = {
            "schema_version": 1, "type": "WORLD_METRIC_TILE",
            "city_id": city_id, "year": year, "id": tile_id(i, j),
            "origin_east_m": i * SIZE_M, "origin_north_m": j * SIZE_M,
            "tile_size_m": SIZE_M,
            "features": sorted(tiles[(i, j)], key=lambda feat: feat["id"]),
        }
        (output_dir / (tile_id(i, j) + ".json")).write_text(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n",
            encoding="utf-8",
        )
    (output_dir / "manifest.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def cli(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--city-id", required=True)
    p.add_argument("--source-id", required=True)
    p.add_argument("--source-url", required=True)
    p.add_argument("--license", dest="license_id", required=True)
    p.add_argument("--source-crs", choices=sorted(VALID_CRS), required=True)
    p.add_argument("--anchor-lon", type=float, required=True)
    p.add_argument("--anchor-lat", type=float, required=True)
    p.add_argument("--year", choices=sorted(VALID_YEARS), required=True)
    p.add_argument("--internal-preview", action="store_true")
    a = p.parse_args(argv)
    try:
        result = build(
            a.input, a.output_dir, city_id=a.city_id, source_crs=a.source_crs,
            anchor_lon=a.anchor_lon, anchor_lat=a.anchor_lat,
            source_id=a.source_id, source_url=a.source_url,
            license_id=a.license_id, year=a.year,
            internal_preview=a.internal_preview,
        )
    except (GeoETLError, OSError, ValueError) as exc:
        print(f"GEODATA ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
