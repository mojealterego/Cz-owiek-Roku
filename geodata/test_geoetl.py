"""Regression tests: metre-accurate PL/CZ point geometry + tile clipping."""
from __future__ import annotations

import hashlib
import itertools
import json
import math
import tempfile
import unittest
from pathlib import Path

from pyproj import Geod, Transformer
from shapely.geometry import LineString, Polygon
from geodata.geoetl import GeoETLError, build, grid_index, metric_transformer, tile_id, SIZE_M

PL = (18.6332106, 49.74816)
CZ = (18.62559852404365, 49.746341767306085)
POINTS = Path(__file__).parent / "fixtures" / "transborder_reference_points.geojson"


def call_build(out: Path, source: Path = POINTS, **overrides):
    settings = {
        "city_id": "CIESZYN_TRANSBORDER", "source_crs": "EPSG:4326",
        "anchor_lon": PL[0], "anchor_lat": PL[1],
        "source_id": "LANDMARKS_VERIFIED_PUBLIC_COORDS",
        "source_url": "https://mapy.com/pl/?id=94209443&source=osm",
        "license_id": "SOURCE_REVIEW_PENDING",
        "year": "2025", "internal_preview": True,
    }
    settings.update(overrides)
    return build(source, out, **settings)


class GeoETLTests(unittest.TestCase):
    def test_cross_border_distance_matches_geodesic_within_centimetres(self):
        p = metric_transformer("EPSG:4326", *PL)
        a = p.transform(*PL)
        b = p.transform(*CZ)
        self.assertAlmostEqual(a[0], 0, places=4)
        self.assertAlmostEqual(a[1], 0, places=4)
        metric = math.dist(a, b)
        geodesic = Geod(ellps="WGS84").inv(*PL, *CZ)[2]
        self.assertAlmostEqual(metric, geodesic, delta=0.01)
        self.assertAlmostEqual(metric, 584.696, delta=0.01)

    def test_source_crs_poland_and_czech_roundtrips(self):
        for crs in ("EPSG:2180", "EPSG:5514"):
            forward = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
            v = forward.transform(*CZ)
            local = metric_transformer(crs, *PL).transform(*v)
            expected = metric_transformer("EPSG:4326", *PL).transform(*CZ)
            self.assertAlmostEqual(local[0], expected[0], delta=0.25)
            self.assertAlmostEqual(local[1], expected[1], delta=0.25)

    def test_two_real_points_exported_to_correct_metric_tiles(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            manifest = call_build(out)
            self.assertEqual(manifest["source_features"], 2)
            self.assertEqual(manifest["tile_count"], 2)
            self.assertFalse(manifest["redistribution_allowed"])
            self.assertEqual(manifest["build_status"], "PREVIEW_ONLY_NOT_HISTORICALLY_VERIFIED")
            expected = {
                "CIESZYN_TOWN_HALL": (0, 0),
                "CESKY_TESIN_TOWN_HALL": (-3, -1),
            }
            for name, indices in expected.items():
                data = json.loads((out / (tile_id(*indices) + ".json")).read_text())
                self.assertEqual(data["tile_size_m"], SIZE_M)
                self.assertIn(name, [f["id"] for f in data["features"]])
                self.assertEqual(data["features"][0]["elevation_status"], "UNKNOWN_NO_TERRAIN")
            self.assertEqual(json.loads((out / "manifest.json").read_text())["tile_count"], 2)

    def test_256m_border_seams_and_negative_grid(self):
        self.assertEqual(grid_index(-0.001, -256.001), (-1, -2))
        self.assertEqual(grid_index(256.0, 256.0), (1, 1))
        self.assertEqual(grid_index(0.0, 0.0), (0, 0))
        self.assertEqual(tile_id(-3, -1), "E-000003_N-000001")

    def test_reject_unknown_license_public_exports(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(GeoETLError):
                call_build(Path(tmp) / "out", internal_preview=False)

    def test_rejects_missing_coordinate_references(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(GeoETLError):
                call_build(Path(tmp) / "out", source_crs="EPSG:3857")

    def test_rejects_duplicate_or_invalid_input(self):
        data = json.loads(POINTS.read_text())
        data["features"].append(data["features"][0])
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "bad.geojson"
            f.write_text(json.dumps(data))
            with self.assertRaises(GeoETLError):
                call_build(Path(tmp) / "out", f)

    def test_metric_line_crosses_tile_boundary_without_distance_compression(self):
        with tempfile.TemporaryDirectory() as tmp:
            inp = Path(tmp) / "road.geojson"
            # The two points are ~600m apart, yielding clipped pieces in multiple tiles.
            source = {"type": "FeatureCollection", "features": [
                {"type": "Feature", "id": "ROAD_TEST", "properties": {"kind": "road", "name": "Test path"},
                 "geometry": {"type": "LineString", "coordinates": [list(PL), list(CZ)]}}
            ]}
            inp.write_text(json.dumps(source))
            man = call_build(Path(tmp) / "output", inp)
            self.assertGreater(man["tile_count"], 2)
            pieces = []
            for tilepath in (Path(tmp) / "output").glob("E*.json"):
                d = json.loads(tilepath.read_text())
                for f in d["features"]:
                    self.assertEqual(f["kind"], "road")
                    for east, north in f["coordinates"]:
                        self.assertGreaterEqual(east, -1e-5)
                        self.assertGreaterEqual(north, -1e-5)
                        self.assertLessEqual(east, SIZE_M + 1e-5)
                        self.assertLessEqual(north, SIZE_M + 1e-5)
                    pieces.append(f)
            self.assertGreater(len(pieces), 2)

    def test_source_preservation_and_refusal_to_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "output"
            expected_hash = hashlib.sha256(POINTS.read_bytes()).hexdigest()
            self.assertEqual(call_build(out)["source"]["sha256"], expected_hash)
            with self.assertRaises(GeoETLError):
                call_build(out)


    def test_godot_preview_positions_match_projected_source_to_centimetre(self):
        raw = json.loads(POINTS.read_text(encoding="utf-8"))
        world = Path(__file__).resolve().parents[1] / "godot" / "data" / "world" / "reference_points.json"
        preview = json.loads(world.read_text(encoding="utf-8"))
        self.assertEqual(preview["status"], "TWO_GEOREFERENCED_LANDMARKS_NOT_A_CITY_MODEL")
        self.assertEqual(preview["units"], "meters")
        self.assertEqual(preview["grid_size_m"], SIZE_M)
        self.assertEqual(preview["anchor_wgs84"], {"lon": PL[0], "lat": PL[1]})
        landmarks = {f["id"]: f["geometry"]["coordinates"] for f in raw["features"]}
        placed = {p["id"]: p for p in preview["points"]}
        self.assertEqual(set(landmarks), set(placed))
        transformer = metric_transformer("EPSG:4326", *PL)
        for name, lon_lat in landmarks.items():
            east, north = transformer.transform(*lon_lat)
            self.assertAlmostEqual(placed[name]["east_m"], east, delta=0.01)
            self.assertAlmostEqual(placed[name]["north_m"], north, delta=0.01)

if __name__ == "__main__":
    unittest.main()
