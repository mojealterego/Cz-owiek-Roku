"""Offline validation of official-service metadata and constrained export request."""
from __future__ import annotations
import unittest
from urllib.parse import parse_qs, urlsplit
from geodata.cuzk_dmr5g_fetch import DMRFetchError, export_image_url, validate_service

GOOD = {
    "spatialReference": {"latestWkid": 5514, "latestVcsWkid": 8357},
    "heightModelInfo": {"vertCRS": "Baltic_1957_height", "heightUnit": "meter"},
    "bandCount": 1, "pixelType": "F32",
}

class DMRServiceTests(unittest.TestCase):
    def test_official_crs_and_height_datum_required(self):
        validate_service(GOOD)
        for mod in [
            {"spatialReference": {"latestWkid": 4326, "latestVcsWkid": 8357}},
            {"heightModelInfo": {"vertCRS": "unknown", "heightUnit": "meter"}},
            {"pixelType": "U8"}, {"error": {"code": 403}},
        ]:
            with self.subTest(change=mod), self.assertRaises(DMRFetchError):
                validate_service({**GOOD, **mod})

    def test_export_is_small_raw_geotiff_in_5514(self):
        u = urlsplit(export_image_url())
        args = parse_qs(u.query)
        self.assertEqual(u.scheme, "https")
        self.assertEqual(u.hostname, "ags.cuzk.gov.cz")
        for key, expected in {"bboxSR": "5514", "imageSR": "5514",
                              "size": "450,450", "format": "tiff",
                              "pixelType": "F32", "f": "image"}.items():
            self.assertEqual(args[key], [expected])


if __name__ == "__main__":
    unittest.main()
