"""Test true OSM provenance and correctness without calling the live API."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from geodata.osm_extract import OSMImportError, BOUNDS, extract, source_url, validate_bbox


ROOT = Path(__file__).parent
FIXTURE = ROOT / "fixtures" / "osm_three_real_buildings.xml"


class OSMExtractionTests(unittest.TestCase):
    def test_three_verified_osm_buildings_and_test_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "result.geojson"
            result = extract(FIXTURE, output, bbox=BOUNDS, api_url=source_url(BOUNDS))
            self.assertEqual(result["features"]["buildings"], 3)
            self.assertEqual(result["features"]["roads"], 1)
            self.assertEqual(result["license"], "ODbL-1.0")
            self.assertEqual(result["historic_state"], "CURRENT_DATA_NOT_VERIFIED_FOR_2023_2025")
            data = json.loads(output.read_text())
            by_id = {feat["id"]: feat for feat in data["features"]}
            self.assertEqual(set(by_id), {
                "OSM_W198560340", "OSM_W198560695", "OSM_W198726576", "OSM_W999999"})
            polygon = by_id["OSM_W198560340"]["geometry"]["coordinates"][0]
            self.assertEqual(polygon[0], polygon[-1])
            self.assertEqual(polygon[0], [18.6315029, 49.7487597])

    def test_rejects_unbounded_bbox(self):
        with self.assertRaises(OSMImportError):
            validate_bbox((0, 0, 2, 2))

    def test_refuses_to_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "result.geojson"
            output.write_text("preserve me")
            with self.assertRaises(OSMImportError):
                extract(FIXTURE, output, bbox=BOUNDS, api_url=source_url(BOUNDS))
            self.assertEqual(output.read_text(), "preserve me")

    def test_rejects_unsafe_xml_entities(self):
        text = '''<!DOCTYPE x [<!ENTITY a "bad">]>
<osm version="0.6"><node id="1" lat="0" lon="0"/></osm>'''
        with tempfile.TemporaryDirectory() as tmp:
            inp = Path(tmp) / "bad.xml"
            inp.write_text(text)
            with self.assertRaises(OSMImportError):
                extract(inp, Path(tmp) / "output.geojson", bbox=BOUNDS, api_url=source_url(BOUNDS))


if __name__ == "__main__":
    unittest.main()
