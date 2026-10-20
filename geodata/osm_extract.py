"""Bounded public OSM API XML → canonical, attributed GeoJSON.

Imports only closed building ways and linear highway ways. No invented heights,
multipolygon relations or historical assertions. Public OSM data is ODbL 1.0.
Downloader is limited to one small bbox, capped size, and a descriptive User-Agent.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from defusedxml import ElementTree as SafeET
from shapely.geometry import shape

API = "https://api.openstreetmap.org/api/0.6/map"
MAX_RAW_BYTES = 12 * 1024 * 1024
BOUNDS = (18.6310, 49.7468, 18.6340, 49.7492)
USER_AGENT = "Czlowiek-Roku-geodata-prototype/0.1 (https://github.com/mojealterego/Cz-owiek-Roku)"
SKIP_ROADS = {"proposed", "construction", "abandoned", "razed"}


class OSMImportError(ValueError):
    pass


def validate_bbox(bbox: tuple[float, float, float, float]) -> None:
    if len(bbox) != 4 or not all(isinstance(v, (int, float)) and math.isfinite(v) for v in bbox):
        raise OSMImportError("Invalid numeric bounds")
    west, south, east, north = bbox
    if not (-180 < west < east < 180 and -90 < south < north < 90):
        raise OSMImportError("Invalid bbox order")
    if east - west > 0.02 or north - south > 0.02:
        raise OSMImportError("BBOX exceeds the bounded extraction limits")


def source_url(bbox: tuple[float, float, float, float]) -> str:
    validate_bbox(bbox)
    return API + "?" + urlencode({"bbox": ",".join(f"{v:.7f}" for v in bbox)})


def download_source(target: Path, bbox: tuple[float, float, float, float] = BOUNDS) -> str:
    if target.exists():
        raise OSMImportError("Refusing to overwrite existing raw file")
    url = source_url(bbox)
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/xml"})
    with urlopen(request, timeout=60) as response:
        content = response.read(MAX_RAW_BYTES + 1)
    if not content or len(content) > MAX_RAW_BYTES:
        raise OSMImportError("OSM API response empty or too large")
    if b"<osm" not in content[:500]:
        raise OSMImportError("Response is not OSM XML")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    return url


def extract(source_file: Path, target_file: Path, *, bbox: tuple[float, float, float, float],
            api_url: str) -> dict:
    validate_bbox(bbox)
    if not source_file.exists() or source_file.stat().st_size > MAX_RAW_BYTES:
        raise OSMImportError("OSM XML missing or oversized")
    if target_file.exists():
        raise OSMImportError("Refusing to overwrite GeoJSON")
    data = source_file.read_bytes()
    try:
        root = SafeET.fromstring(data)
    except Exception as exc:
        raise OSMImportError("Unsafe or invalid XML source") from exc
    if root.tag != "osm":
        raise OSMImportError("Not an OSM document")
    nodes: dict[str, list[float]] = {}
    ways = []
    for item in root:
        if item.tag == "node":
            uid = item.get("id", "")
            try:
                lon, lat = float(item.attrib["lon"]), float(item.attrib["lat"])
            except (KeyError, ValueError) as exc:
                raise OSMImportError("Invalid node coordinate") from exc
            if uid in nodes or not (math.isfinite(lon) and math.isfinite(lat)):
                raise OSMImportError("Duplicate node or non-finite coordinate")
            nodes[uid] = [lon, lat]
        elif item.tag == "way":
            ways.append(item)
    features = []
    skipped = {"missing_node": 0, "invalid_polygon": 0, "unclosed_building": 0,
               "non_target": 0, "unsupported_highway": 0}
    counts = {"buildings": 0, "roads": 0}
    for item in ways:
        tags = {e.get("k"): e.get("v") for e in item if e.tag == "tag"}
        building = tags.get("building") not in (None, "no", "demolished")
        highway = tags.get("highway")
        if not building and not highway:
            skipped["non_target"] += 1
            continue
        if highway in SKIP_ROADS and not building:
            skipped["unsupported_highway"] += 1
            continue
        refs = [e.get("ref", "") for e in item if e.tag == "nd"]
        if len(refs) < (4 if building else 2) or any(ref not in nodes for ref in refs):
            skipped["missing_node"] += 1
            continue
        coordinates = [nodes[ref] for ref in refs]
        kind = "building" if building else "road"
        if building:
            if refs[0] != refs[-1]:
                skipped["unclosed_building"] += 1
                continue
            geometry = {"type": "Polygon", "coordinates": [coordinates]}
            polygon = shape(geometry)
            if polygon.is_empty or not polygon.is_valid or polygon.area <= 0:
                skipped["invalid_polygon"] += 1
                continue
        else:
            geometry = {"type": "LineString", "coordinates": coordinates}
        uid = item.get("id", "")
        if not uid.isdecimal() or len(uid) > 20:
            raise OSMImportError("Invalid OSM way ID")
        name = tags.get("name", "")
        if not isinstance(name, str) or len(name) > 160:
            name = name[:160] if isinstance(name, str) else ""
        features.append({
            "type": "Feature",
            "id": "OSM_W" + uid,
            "properties": {"kind": kind, "name": name},
            "geometry": geometry,
        })
        counts["buildings" if building else "roads"] += 1
    if not features:
        raise OSMImportError("OSM area contains no valid street or building outlines")
    # Keep raw extraction status separate from fictional/historical scene year.
    provenance = {
        "schema_version": 1,
        "source": "OpenStreetMap contributors",
        "license": "ODbL-1.0",
        "attribution": "© OpenStreetMap contributors — https://www.openstreetmap.org/copyright",
        "source_url": api_url,
        "source_sha256": hashlib.sha256(data).hexdigest(),
        "downloaded_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "bbox_wgs84": list(bbox),
        "historic_state": "CURRENT_DATA_NOT_VERIFIED_FOR_2023_2025",
        "node_count": len(nodes), "way_count": len(ways),
        "features": counts, "skipped": skipped,
        "relation_multipolygon_support": "NOT_IMPLEMENTED",
    }
    output = {"type": "FeatureCollection", "features": sorted(features, key=lambda f: f["id"]),
              "metadata": provenance}
    target_file.parent.mkdir(parents=True, exist_ok=True)
    target_file.write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":"),
                                      sort_keys=True) + "\n", encoding="utf-8")
    return provenance


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-xml", type=Path, required=True)
    parser.add_argument("--geojson", type=Path, required=True)
    parser.add_argument("--fetch", action="store_true")
    parser.add_argument("--bbox", nargs=4, type=float, default=list(BOUNDS),
                        metavar=("WEST", "SOUTH", "EAST", "NORTH"))
    args = parser.parse_args()
    bbox = tuple(args.bbox)
    url = source_url(bbox)
    if args.fetch:
        download_source(args.raw_xml, bbox)
    provenance = extract(args.raw_xml, args.geojson, bbox=bbox, api_url=url)
    print(json.dumps(provenance, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
