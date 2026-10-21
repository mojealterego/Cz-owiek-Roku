"""Refresh OSM building height metadata without silently moving verified outlines.

Takes an existing fixed-footprint GeoJSON and a newly fetched GeoJSON for the
identical bounded OSM area. Refuses any geometry or source-ID drift; tags remain
OSM-reported, NOT independently surveyed. Never converts storeys to metres.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

HEIGHT_PROPS = (
    "height_m", "height_source", "height_status",
    "building_levels", "levels_status",
)


class HeightRefreshError(ValueError):
    pass


def enrich(original_file: Path, refreshed_file: Path, output_file: Path) -> dict:
    if output_file.exists():
        raise HeightRefreshError("Output file already exists")
    original = json.loads(original_file.read_text(encoding="utf-8"))
    recent = json.loads(refreshed_file.read_text(encoding="utf-8"))
    if original.get("type") != "FeatureCollection" or recent.get("type") != "FeatureCollection":
        raise HeightRefreshError("Expected GeoJSON FeatureCollections")
    base = {feature["id"]: feature for feature in original["features"]}
    fresh = {feature["id"]: feature for feature in recent["features"]}
    if len(base) != len(original["features"]) or len(fresh) != len(recent["features"]):
        raise HeightRefreshError("Repeated source identifiers")
    if set(base) != set(fresh):
        raise HeightRefreshError("OSM source changed way IDs; require manual full refresh")
    if original["metadata"].get("license") != "ODbL-1.0":
        raise HeightRefreshError("Only openly attributed OSM licensed source accepted")
    coverage = {"explicit_height": 0, "levels_without_height": 0, "unknown": 0}
    for feature in original["features"]:
        current = fresh[feature["id"]]
        if feature["geometry"] != current["geometry"]:
            raise HeightRefreshError("Changed OSM coordinates; require manual full geometry import")
        if feature["properties"].get("kind") != current["properties"].get("kind"):
            raise HeightRefreshError("Building/road classification drift")
        props = feature["properties"]
        for key in HEIGHT_PROPS:
            props.pop(key, None)
        if props.get("kind") != "building":
            continue
        props.update({key: current["properties"][key] for key in HEIGHT_PROPS
                      if key in current["properties"]})
        if "height_m" in props:
            coverage["explicit_height"] += 1
        elif "building_levels" in props:
            coverage["levels_without_height"] += 1
        else:
            coverage["unknown"] += 1
    meta = original["metadata"]
    meta["height_tag_refresh"] = {
        "source": "OpenStreetMap contributors",
        "license": "ODbL-1.0",
        "source_xml_sha256": recent["metadata"]["source_sha256"],
        "retrieved_at_utc": recent["metadata"]["downloaded_at_utc"],
        "geometry_changed": False,
        "height_coverage": coverage,
        "ground_elevation_available": False,
        "historic_2023_2025_validated": False,
    }
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(original, ensure_ascii=False,
                                      sort_keys=True, separators=(",", ":")) + "\n",
                           encoding="utf-8")
    return coverage


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--refreshed", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(enrich(args.source, args.refreshed, args.output), sort_keys=True))


if __name__ == "__main__":
    main()
