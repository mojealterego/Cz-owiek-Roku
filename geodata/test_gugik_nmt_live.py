"""Offline WCS GetCoverage metadata checks; never invent source DEM."""
import unittest
from urllib.parse import parse_qs, urlparse
from geodata.gugik_nmt_live import (
    PolishNMTError, BBOX, COVERAGE_ID, coverage_url, parse_description,
)
DESC = b'''<?xml version="1.0"?>
<wcs:CoverageDescriptions xmlns:wcs="http://www.opengis.net/wcs/2.0"
 xmlns:gml="http://www.opengis.net/gml/3.2">
<wcs:CoverageDescription><wcs:CoverageId>DTM_PL-KRON86-NH_TIFF</wcs:CoverageId>
<gml:boundedBy><gml:Envelope axisLabels="x y" srsName="http://www.opengis.net/def/crs/EPSG/0/2180" srsDimension="2">
<gml:lowerCorner>400000 100000</gml:lowerCorner>
<gml:upperCorner>600000 400000</gml:upperCorner>
</gml:Envelope></gml:boundedBy></wcs:CoverageDescription>
</wcs:CoverageDescriptions>'''

class WCSNMTTests(unittest.TestCase):
    def test_exact_covered_envelope_and_vertical_pending(self):
        d=parse_description(DESC)
        self.assertEqual(d["axis_labels"], ["x","y"])
        self.assertEqual(d["horizontal_crs"], "EPSG:2180")
        self.assertFalse(d["vertical_datum_independently_verified"])

    def test_build_bounded_geotiff_getcoverage(self):
        u=urlparse(coverage_url(["x","y"]))
        q=parse_qs(u.query)
        self.assertEqual(q["REQUEST"], ["GetCoverage"])
        self.assertEqual(q["COVERAGEID"], [COVERAGE_ID])
        self.assertEqual(q["FORMAT"], ["image/tiff"])
        self.assertEqual(q["SUBSET"], [f"x({BBOX[0]},{BBOX[2]})",
                                       f"y({BBOX[1]},{BBOX[3]})"])

    def test_server_declared_reverse_yx_order_keeps_coordinate_semantics(self):
        from urllib.parse import parse_qs, urlparse
        q = parse_qs(urlparse(coverage_url(["y", "x"])).query)
        self.assertEqual(q["SUBSET"], [f"y({BBOX[1]},{BBOX[3]})",
                                       f"x({BBOX[0]},{BBOX[2]})"])

    def test_rejects_unknown_axis_order_or_crs(self):
        with self.assertRaises(PolishNMTError):
            coverage_url(["latitude","longitude"])
        with self.assertRaises(PolishNMTError):
            parse_description(DESC.replace(b"2180", b"4326"))


if __name__ == "__main__":
    unittest.main()
