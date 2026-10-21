"""Test-only synthetic DEM. Never commit synthetic terrain as an actual city."""
from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.transform import from_origin

from geodata.terrain_geotiff import TerrainError, export_geotiff


def source_geotiff(root: Path, *, nodata: bool = False) -> Path:
    px, py = Transformer.from_crs("EPSG:4326", "EPSG:2180",
                                  always_xy=True).transform(18.6332106, 49.74816)
    source = root / "SYNTHETIC_TEST_ONLY_NOT_ACTUAL_CIESZYN.tif"
    arr = np.full((130, 130), 307.5, dtype="float32")
    if nodata:
        arr[0:10, 0:10] = -9999.0
    with rasterio.open(source, "w", driver="GTiff", height=130, width=130,
                       count=1, dtype="float32", crs="EPSG:2180",
                       transform=from_origin(px - 650, py + 650, 10, 10),
                       nodata=-9999.0) as dst:
        dst.write(arr, 1)
    return source


def build(src: Path, out: Path, **overrides):
    kwargs = {
        "city_id": "CIESZYN_TEST_ONLY", "source_id": "SYNTHETIC_QA_RASTER",
        "source_url": "https://example.org/test-only-do-not-publish",
        "license_id": "TEST_ONLY", "vertical_datum": "TEST_LOCAL_DATUM",
        "source_epoch": "2024", "west": -1, "east": 0,
        "south": -1, "north": 0, "spacing_m": 32, "internal_preview": True,
    }
    kwargs.update(overrides)
    return export_geotiff(src, out, **kwargs)


class TerrainTests(unittest.TestCase):
    def test_synthetic_tiles_have_exact_metric_grid_and_source_value(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); source = source_geotiff(root)
            result = build(source, root / "tiles")
            self.assertEqual(result["tile_count"], 4)
            self.assertEqual(result["vertical_registration_to_game"], "NOT_VERIFIED")
            self.assertEqual(result["source_crs"], "EPSG:2180")
            self.assertGreater(result["valid_sample_count"], 0)
            self.assertFalse(result["historical_facades_validated"])
            data = json.loads((root / "tiles" / "E+000000_N+000000.json").read_text())
            self.assertEqual(data["grid_width"], 9)
            self.assertEqual(data["grid_height"], 9)
            self.assertEqual(len(data["heights_m"]), 81)
            self.assertTrue(all(h == 307.5 for h in data["heights_m"] if h is not None))

    def test_shared_tile_edges_are_bit_identical(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); build(source_geotiff(root), root / "tiles")
            a = json.loads((root / "tiles" / "E-000001_N+000000.json").read_text())
            b = json.loads((root / "tiles" / "E+000000_N+000000.json").read_text())
            width = a["grid_width"]
            self.assertEqual([a["heights_m"][y * width + width - 1] for y in range(width)],
                             [b["heights_m"][y * width] for y in range(width)])

    def test_nodata_retained_and_not_made_up(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            source = source_geotiff(root, nodata=True)
            out = root / "tiles"
            result = build(source, out, west=-2, east=1, south=-2, north=1)
            self.assertGreater(result["nodata_sample_count"], 0)
            found = [h for p in out.glob("E*.json")
                     for h in json.loads(p.read_text())["heights_m"] if h is None]
            self.assertTrue(found)

    def test_license_and_datum_required(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); source=source_geotiff(root)
            with self.assertRaises(TerrainError):
                build(source, root / "no", internal_preview=False)
            with self.assertRaises(TerrainError):
                build(source, root / "no", vertical_datum="")

    def test_refuses_overwrite_and_invalid_grid(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); source=source_geotiff(root)
            out=root / "out"; build(source, out)
            with self.assertRaises(TerrainError):
                build(source, out)
            with self.assertRaises(TerrainError):
                build(source, root / "badgrid", spacing_m=30)

    def test_czech_source_crs_roundtrip_in_shared_city_frame(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            # Set up a REAL horizontal Czech coordinate reference with SYNTHETIC elevations.
            x, y = Transformer.from_crs("EPSG:4326", "EPSG:5514",
                                        always_xy=True).transform(18.62559852404365,
                                                                   49.746341767306085)
            tif=root / "SYNTHETIC_CZ.tif"
            with rasterio.open(tif,"w",driver="GTiff",height=200,width=200,
                               count=1,dtype="float32",crs="EPSG:5514",
                               transform=from_origin(x-1000,y+1000,10,10),
                               nodata=-9999) as ds:
                ds.write(np.full((200,200), 270.0,dtype="float32"),1)
            result=build(tif,root/"czout",city_id="CESKY_TESIN_TEST_ONLY",
                         west=-4,east=-2,south=-2,north=0,
                         vertical_datum="TEST_CZ_DATUM")
            self.assertEqual(result["source_crs"], "EPSG:5514")
            self.assertGreater(result["valid_sample_count"], 0)


if __name__ == "__main__":
    unittest.main()
