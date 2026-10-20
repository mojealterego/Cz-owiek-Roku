"""Executable tests: WORLD 1:1 contract and no invented completed cities."""
from __future__ import annotations

import json
import math
import unittest
from pathlib import Path

from world_grid import TILE_SIZE_M, GeoGridError, local_offsets_m, tile_for

DATA = Path(__file__).resolve().parents[1] / "data" / "world" / "city_reconstruction_manifest.json"
EXPECTED_CITIES = {
    "PL-CIESZYN", "CZ-CESKY-TESIN", "PL-BIELSKO-BIALA", "PL-ZORY",
    "PL-WARSZAWA", "PL-LUBLIN", "PL-LECZNA",
}


class WorldGridTests(unittest.TestCase):
    def test_square_tile_area_is_metric(self) -> None:
        self.assertEqual(TILE_SIZE_M, 256.0)
        self.assertEqual(tile_for(255.999, 255.999).identifier, "E+000000_N+000000")
        self.assertEqual(tile_for(256, 256).identifier, "E+000001_N+000001")
        self.assertEqual(tile_for(-0.001, -256.001).identifier, "E-000001_N-000002")

    def test_roundtrip_local_offsets_and_no_distance_scaling(self) -> None:
        coordinates = [(-513.3, 2048.1), (-256.0, -256.0), (-0.01, 0), (0, 0), (256, 256)]
        for east, north in coordinates:
            tile, e_local, n_local = local_offsets_m(east, north)
            self.assertAlmostEqual(tile.origin_east_m + e_local, east, places=8)
            self.assertAlmostEqual(tile.origin_north_m + n_local, north, places=8)
            self.assertTrue(0 <= e_local < TILE_SIZE_M)
            self.assertTrue(0 <= n_local < TILE_SIZE_M)

    def test_refuse_invalid_units(self) -> None:
        for bad in (float("nan"), float("inf"), float("-inf"), "49.8", None, True):
            with self.subTest(bad=bad):
                with self.assertRaises(GeoGridError):
                    tile_for(bad, 0)

    def test_manifest_is_explicitly_not_finished(self) -> None:
        doc = json.loads(DATA.read_text(encoding="utf-8"))
        self.assertEqual(doc["geometry_contract"]["game_units_per_meter"], 1)
        self.assertTrue(doc["geometry_contract"]["no_artificial_distance_compression"])
        self.assertEqual(doc["geometry_contract"]["canonical_tile_size_m"], TILE_SIZE_M)
        self.assertEqual(doc["mode"], "PRODUCTION_REQUIREMENT_NOT_IMPLEMENTED")
        self.assertEqual(doc["geometry_contract"]["coordinate_transform_status"], "NOT_IMPLEMENTED")
        ids = [item["id"] for item in doc["locations"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(EXPECTED_CITIES.issubset(ids))
        for location in doc["locations"]:
            self.assertIn(location["type"], ("city", "site"))
            self.assertIn(location["country"], ("PL", "CZ"))
            self.assertEqual(location["city_build_status"], "NOT_STARTED")
            self.assertFalse(location["geodata_imported"])
            self.assertFalse(location["historical_reconstruction_verified"])
            self.assertIsNone(location["verified_geographic_anchor"])
            self.assertIsNone(location["acceptance_report"])
            self.assertEqual(location["scenes_from_book"], [])
            self.assertEqual(location["source_coverage_status"], "NEEDS_CHAPTER_PAGE_MAPPING")

    def test_historical_snapshots_have_story_years(self) -> None:
        manifest = json.loads(DATA.read_text(encoding="utf-8"))
        self.assertEqual(
            manifest["geometry_contract"]["historical_scene_snapshots"],
            ["2023", "2024", "2025"],
        )

if __name__ == "__main__":
    unittest.main()
