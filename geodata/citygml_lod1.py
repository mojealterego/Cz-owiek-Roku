"""Strict offline import of real GUGiK CityGML LoD1 2024 geometry.

No guessed height, terrain datum, axis order, historical facade or building.
Accept only GML Solid polygon rings with 3D coordinates and explicit input CRS.
Exports source-preserving, metrically referenced QA geometry; not production art.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

from defusedxml import ElementTree as XML
from pyproj import CRS, Transformer

MAX_BYTES = 64 * 1024 * 1024
MAX_BUILDINGS = 20000
MAX_RINGS_PER_BUILDING = 500
MAX_VERTICES_PER_RING = 2000
MAX_RADIUS_M = 30000
VALID_SOURCE_CRS = {
    "EPSG:2180", "EPSG:2177", "EPSG:2178", "EPSG:2179", "EPSG:4326"
}
VALID_AXES = {"east-north", "north-east"}
ID_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_.:-]{0,127}$")


class CityGMLError(ValueError):
    pass


def localname(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _source_crs_from_gml(root: Any) -> str | None:
    for e in root.iter():
        value = e.get("srsName")
        if value:
            code = value.rsplit(":", 1)[-1]
            if code.isdecimal():
                return "EPSG:" + code
    return None


def _ring(element: Any, to_local: Transformer, axis_order: str) -> list[list[float]]:
    candidates = [e for e in element.iter() if localname(e.tag) == "posList"]
    if len(candidates) != 1:
        raise CityGMLError("Expected exactly one gml:posList per linear ring")
    poslist = candidates[0]
    if poslist.get("srsDimension", "3") != "3":
        raise CityGMLError("Only 3-dimensional GML rings are supported")
    raw = (poslist.text or "").split()
    if len(raw) % 3 != 0 or not (12 <= len(raw) <= MAX_VERTICES_PER_RING * 3):
        raise CityGMLError("Invalid 3D GML ring coordinate count")
    points = []
    for i in range(0, len(raw), 3):
        try:
            x, y, elevation = (float(raw[i]), float(raw[i + 1]), float(raw[i + 2]))
        except ValueError as exc:
            raise CityGMLError("Non-numeric GML polygon") from exc
        if not all(math.isfinite(v) for v in (x, y, elevation)):
            raise CityGMLError("Non-finite GML geometry")
        if axis_order == "north-east":
            x, y = y, x
        east, north = to_local.transform(x, y)
        if not all(math.isfinite(v) for v in (east, north)):
            raise CityGMLError("Invalid geographic reprojection")
        if math.hypot(east, north) > MAX_RADIUS_M:
            raise CityGMLError("Geometry too far from source-verified Cieszyn anchor")
        points.append([round(east, 5), round(north, 5), round(elevation, 4)])
    if points[0] != points[-1]:
        raise CityGMLError("Unclosed GML polygon ring")
    if len(set(tuple(x) for x in points[:-1])) < 3:
        raise CityGMLError("Degenerate GML polygon")
    return points


def import_citygml(
    source: Path, destination: Path, *, source_crs: str,
    axis_order: str, anchor_lon: float = 18.6332106,
    anchor_lat: float = 49.74816, snapshot_year: int = 2024
) -> dict[str, Any]:
    if source_crs not in VALID_SOURCE_CRS or axis_order not in VALID_AXES:
        raise CityGMLError("Explicit permitted source CRS and axis order required")
    if snapshot_year not in (2019, 2021, 2022, 2024):
        raise CityGMLError("Use a documented official CityGML dataset year")
    if destination.exists():
        raise CityGMLError("Refusing output overwrite")
    if not source.is_file() or not (0 < source.stat().st_size <= MAX_BYTES):
        raise CityGMLError("Missing or oversized CityGML source (64 MiB per chunk limit)")
    data = source.read_bytes()
    try:
        root = XML.fromstring(data)
    except Exception as exc:
        raise CityGMLError("Malformed or unsafe CityGML XML") from exc
    if localname(root.tag) != "CityModel":
        raise CityGMLError("CityGML CityModel root required")
    advertised_crs = _source_crs_from_gml(root)
    if advertised_crs and advertised_crs != source_crs:
        raise CityGMLError(f"CRS mismatch: source announces {advertised_crs}")
    local_crs = CRS.from_proj4(
        f"+proj=aeqd +lat_0={anchor_lat:.12f} +lon_0={anchor_lon:.12f} "
        "+datum=WGS84 +units=m +no_defs"
    )
    to_local = Transformer.from_crs(source_crs, local_crs, always_xy=True)
    objects: list[dict[str, Any]] = []
    seen: set[str] = set()
    for b in root.iter():
        if localname(b.tag) != "Building":
            continue
        if len(objects) >= MAX_BUILDINGS:
            raise CityGMLError("Excessive number of CityGML buildings")
        gml_id = next((value for key, value in b.attrib.items() if localname(key) == "id"), None)
        if not gml_id or not ID_PATTERN.fullmatch(gml_id) or gml_id in seen:
            raise CityGMLError("Missing, invalid or duplicate CityGML building ID")
        seen.add(gml_id)
        solids = [c for c in b if localname(c.tag) == "lod1Solid"]
        if len(solids) != 1:
            continue  # Other LoD / building without LoD1 — no fabricated geometry.
        rings: list[list[list[float]]] = []
        for poly in solids[0].iter():
            if localname(poly.tag) != "Polygon":
                continue
            exterior = [x for x in poly if localname(x.tag) == "exterior"]
            if len(exterior) != 1:
                raise CityGMLError(f"Polygon missing exterior in {gml_id}")
            rings.append(_ring(exterior[0], to_local, axis_order))
            if len(rings) > MAX_RINGS_PER_BUILDING:
                raise CityGMLError("Too many LoD1 polygon surfaces")
        if not rings:
            continue
        heights = [c for c in b if localname(c.tag) == "measuredHeight"]
        measured: float | None = None
        if heights:
            try:
                measured = float(heights[0].text or "")
            except ValueError as exc:
                raise CityGMLError("Invalid measuredHeight") from exc
            unit = heights[0].get("uom", "m")
            if unit not in ("m", "metre", "meter") or not math.isfinite(measured) or not (0.5 <= measured <= 300):
                raise CityGMLError("Invalid measuredHeight unit or physical range")
        floor_z = min(v[2] for ring in rings for v in ring)
        roof_z = max(v[2] for ring in rings for v in ring)
        objects.append({
            "id": gml_id,
            "source": "GUGiK_CityGML_LoD1",
            "source_year": snapshot_year,
            "measured_height_m": measured,
            "height_reference": "GUGiK_LiDAR_MEDIAN_APPROXIMATE" if measured is not None else "GML_SURFACE_COORDINATES_ONLY",
            "min_source_elevation_m": floor_z,
            "max_source_elevation_m": roof_z,
            "polygon_rings": rings,
            "geometry_status": "SOURCE_3D_UNVERIFIED_VISUAL_RECONSTRUCTION",
        })
    manifest = {
        "schema_version": 1, "type": "GUGIK_CITYGML_LOD1_GEOREFERENCED_QA",
        "source_sha256": hashlib.sha256(data).hexdigest(),
        "source_crs": source_crs, "gml_advertised_crs": advertised_crs,
        "source_axis_order_explicit": axis_order,
        "source_year": snapshot_year,
        "anchor_wgs84": {"lon": anchor_lon, "lat": anchor_lat},
        "vertical_datum": "REQUIRES_SOURCE_METADATA_VERIFICATION",
        "world_scale_m_per_unit": 1.0,
        "terrain_imported": False, "historical_facades_validated": False,
        "official_data_obtained": True,
        "building_count": len(objects),
        "measured_height_count": sum(1 for x in objects if x["measured_height_m"] is not None),
        "buildings": objects,
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(manifest, sort_keys=True, ensure_ascii=False,
                                      separators=(",", ":")) + "\n", encoding="utf-8")
    return {k: v for k, v in manifest.items() if k != "buildings"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-crs", choices=sorted(VALID_SOURCE_CRS), required=True)
    parser.add_argument("--axis-order", choices=sorted(VALID_AXES), required=True)
    parser.add_argument("--year", type=int, choices=[2019, 2021, 2022, 2024], default=2024)
    args = parser.parse_args()
    result = import_citygml(args.input, args.output, source_crs=args.source_crs,
                            axis_order=args.axis_order, snapshot_year=args.year)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
