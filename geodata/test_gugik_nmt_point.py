import unittest
from geodata.gugik_nmt_point import PolishPointError, parse_height, sample_one, point_url
from urllib.parse import parse_qs, urlparse

class PointHeightTests(unittest.TestCase):
    def test_strict_numeric_response(self):
        self.assertEqual(parse_height(b"278.3"), 278.3)
        self.assertEqual(parse_height(b"301,23\n"), 301.23)

    def test_errors_are_not_terrain_values(self):
        for data in (b"0", b"-9999", b"<html>500</html>", b"555555", b"", b"error", b"{}".replace(b"",b"")):
            with self.subTest(data=data), self.assertRaises(PolishPointError):
                parse_height(data)

    def test_api_parameter_axis_order_is_not_always_xy(self):
        q = parse_qs(urlparse(point_url(473584.178, 209041.273)).query)
        self.assertEqual(q["x"], ["209041.273"])
        self.assertEqual(q["y"], ["473584.178"])

    def test_outside_city_refused_before_network(self):
        with self.assertRaises(PolishPointError):
            sample_one(200000, 200000)

if __name__ == "__main__":
    unittest.main()
