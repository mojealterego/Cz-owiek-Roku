"""CityGML LoD1 validation with a deliberately synthetic test-only fixture."""
import json
import tempfile
import unittest
from pathlib import Path
from pyproj import Transformer
from geodata.citygml_lod1 import CityGMLError, import_citygml

TEMPLATE = '''<?xml version="1.0" encoding="UTF-8"?>
<core:CityModel xmlns:core="http://www.opengis.net/citygml/2.0"
 xmlns:bldg="http://www.opengis.net/citygml/building/2.0"
 xmlns:gml="http://www.opengis.net/gml">
 <core:cityObjectMember>
 <bldg:Building gml:id="TEST_SYNTHETIC_NOT_CIESZYN">
  <bldg:measuredHeight uom="m">10</bldg:measuredHeight>
  <bldg:lod1Solid><gml:Solid srsName="EPSG:2180"><gml:exterior>
   <gml:CompositeSurface><gml:surfaceMember><gml:Polygon>
    <gml:exterior><gml:LinearRing><gml:posList>{coords}</gml:posList>
    </gml:LinearRing></gml:exterior>
   </gml:Polygon></gml:surfaceMember></gml:CompositeSurface>
  </gml:exterior></gml:Solid></bldg:lod1Solid>
 </bldg:Building></core:cityObjectMember>
</core:CityModel>'''


class CityGMLTests(unittest.TestCase):
    def fixture(self):
        p = Transformer.from_crs("EPSG:4326", "EPSG:2180", always_xy=True)
        x, y = p.transform(18.6332106, 49.74816)
        points = [(x,y,300), (x+10,y,300), (x+10,y+15,310),
                  (x,y+15,310), (x,y,300)]
        return TEMPLATE.format(coords=" ".join(str(v) for point in points for v in point))

    def test_real_crs_with_synthetic_geometry_is_metric_and_not_marked_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, result = Path(tmp)/"fixture.gml", Path(tmp)/"converted.json"
            source.write_text(self.fixture())
            summary = import_citygml(source,result,source_crs="EPSG:2180",axis_order="east-north")
            record = json.loads(result.read_text())
            self.assertEqual(summary["building_count"], 1)
            self.assertEqual(summary["measured_height_count"], 1)
            self.assertEqual(record["buildings"][0]["measured_height_m"], 10)
            self.assertAlmostEqual(record["buildings"][0]["polygon_rings"][0][0][0], 0, delta=0.1)
            self.assertFalse(record["terrain_imported"])
            self.assertFalse(record["historical_facades_validated"])
            self.assertEqual(record["vertical_datum"], "REQUIRES_SOURCE_METADATA_VERIFICATION")
            self.assertEqual(record["buildings"][0]["source"], "GUGiK_CityGML_LoD1")

    def test_invalid_axis_reference_is_not_silently_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            src=Path(tmp)/"fixture.gml"; src.write_text(self.fixture())
            with self.assertRaises(CityGMLError):
                import_citygml(src,Path(tmp)/"out.json",source_crs="EPSG:2180",axis_order="north-east")

    def test_duplicate_or_unclosed_geometry_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            src=Path(tmp)/"bad.gml"
            src.write_text(self.fixture().replace("TEST_SYNTHETIC_NOT_CIESZYN","BAD"))
            text=src.read_text();start=text.index("<gml:posList>")+len("<gml:posList>")
            end=text.index("</gml:posList>")
            tokens=text[start:end].split()
            tokens[-3:]=["0","0","0"]
            src.write_text(text[:start]+" ".join(tokens)+text[end:])
            with self.assertRaises(CityGMLError):
                import_citygml(src,Path(tmp)/"out.json",source_crs="EPSG:2180",axis_order="east-north")

    def test_disallows_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            src=Path(tmp)/"fixture.gml"; dst=Path(tmp)/"result.json"
            src.write_text(self.fixture());dst.write_text("keep")
            with self.assertRaises(CityGMLError):
                import_citygml(src,dst,source_crs="EPSG:2180",axis_order="east-north")
            self.assertEqual(dst.read_text(),"keep")


if __name__=="__main__":
    unittest.main()
