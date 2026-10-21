"""Height refresh must never change original source geometry or imply measurements."""
import json
import tempfile
import unittest
from pathlib import Path

from geodata.enrich_height_tags import HeightRefreshError, enrich


class HeightRefreshTests(unittest.TestCase):
    def records(self):
        def record(height=None, floors=None):
            props = {"kind": "building", "name": ""}
            if height is not None:
                props.update(height_m=height, height_source="OSM_HEIGHT_TAG",
                             height_status="OSM_REPORTED_UNVERIFIED")
            if floors is not None:
                props.update(building_levels=floors,
                             levels_status="OSM_LEVEL_COUNT_ONLY_NOT_HEIGHT")
            return {"type": "Feature", "id": "OSM_W123",
                    "properties": props,
                    "geometry": {"type": "Polygon", "coordinates": [
                        [[18.6, 49.7], [18.7, 49.7], [18.6, 49.8], [18.6, 49.7]]]}}
        def wrap(f):
            return {"type": "FeatureCollection", "features": [f],
                    "metadata": {"license": "ODbL-1.0",
                                 "source_sha256": "f00", "downloaded_at_utc": "2026-10-21T00:00:00Z"}}
        return wrap(record()), wrap(record(14.25, 3))

    def test_only_explicit_height_is_retained(self):
        original, recent = self.records()
        with tempfile.TemporaryDirectory() as td:
            source, updated, target = (Path(td) / name for name in ("a.json", "b.json", "c.json"))
            source.write_text(json.dumps(original))
            updated.write_text(json.dumps(recent))
            coverage = enrich(source, updated, target)
            result = json.loads(target.read_text())
            self.assertEqual(coverage["explicit_height"], 1)
            self.assertEqual(result["features"][0]["properties"]["height_m"], 14.25)
            self.assertEqual(result["features"][0]["geometry"], original["features"][0]["geometry"])
            self.assertFalse(result["metadata"]["height_tag_refresh"]["historic_2023_2025_validated"])

    def test_modified_geometry_is_rejected(self):
        original, recent = self.records()
        recent["features"][0]["geometry"]["coordinates"][0][0][0] += 0.001
        with tempfile.TemporaryDirectory() as td:
            source, updated, target = (Path(td) / name for name in ("a.json", "b.json", "c.json"))
            source.write_text(json.dumps(original))
            updated.write_text(json.dumps(recent))
            with self.assertRaises(HeightRefreshError):
                enrich(source, updated, target)
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
