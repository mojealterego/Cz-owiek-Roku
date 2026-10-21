"""Unit tests for zero-assumption GUGiK WCS capabilities discovery."""
import unittest
from geodata.gugik_wcs_probe import GUGiKWCSProbeError, parse_capabilities

WCS2 = b'''<?xml version="1.0"?>
<wcs:Capabilities xmlns:wcs="http://www.opengis.net/wcs/2.0"
 xmlns:ows="http://www.opengis.net/ows/2.0" version="2.0.1">
 <wcs:Contents><wcs:CoverageSummary>
 <wcs:CoverageId>NMT_COVERAGE_TEST_ONLY</wcs:CoverageId>
 </wcs:CoverageSummary></wcs:Contents>
 <wcs:ServiceMetadata><wcs:formatSupported>image/tiff</wcs:formatSupported>
 </wcs:ServiceMetadata>
</wcs:Capabilities>'''

WCS1 = b'''<?xml version="1.0"?>
<WCS_Capabilities version="1.0.0">
<ContentMetadata><CoverageOfferingBrief>
<name>TEST_ONLY_DTM</name>
</CoverageOfferingBrief></ContentMetadata>
</WCS_Capabilities>'''

class ProbeTests(unittest.TestCase):
    def test_parse_wcs2_and_avoid_fake_terrain(self):
        v=parse_capabilities(WCS2)
        self.assertEqual(v["coverage_ids"], ["NMT_COVERAGE_TEST_ONLY"])
        self.assertEqual(v["advertised_formats"], ["image/tiff"])
        self.assertFalse(v["source_geometry_imported"])
        self.assertEqual(v["vertical_datum_status"], "NOT_VERIFIED_FROM_CAPABILITIES")

    def test_parse_wcs1(self):
        v=parse_capabilities(WCS1)
        self.assertEqual(v["coverage_ids"], ["TEST_ONLY_DTM"])

    def test_rejects_unsafe_xml_and_missing_coverage(self):
        for data in (
          b'<!DOCTYPE x [<!ENTITY x "evil">]><Capabilities>&x;</Capabilities>',
          b'<Capabilities version="2.0.1"><Contents/></Capabilities>',
          b'<html>server error</html>',
        ):
            with self.subTest(data=data[:40]), self.assertRaises(GUGiKWCSProbeError):
                parse_capabilities(data)


if __name__ == "__main__":
    unittest.main()
