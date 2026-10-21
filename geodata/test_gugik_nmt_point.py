import unittest
from geodata.gugik_nmt_point import PolishPointError, parse_height, sample_one

class PointHeightTests(unittest.TestCase):
    def test_strict_numeric_response(self):
        self.assertEqual(parse_height(b"278.3"), 278.3)
        self.assertEqual(parse_height(b"301,23\n"), 301.23)

    def test_errors_are_not_terrain_values(self):
        for data in (b"0", b"-9999", b"<html>500</html>", b"555555", b"", b"error", b"{}".replace(b"",b"")):
            with self.subTest(data=data), self.assertRaises(PolishPointError):
                parse_height(data)

    def test_outside_city_refused_before_network(self):
        with self.assertRaises(PolishPointError):
            sample_one(200000, 200000)

if __name__ == "__main__":
    unittest.main()
