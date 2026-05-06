import unittest

from museum_gallery_ai.geometry import crossing_direction, point_in_polygon


class GeometryTests(unittest.TestCase):
    def test_point_in_polygon_includes_inside_outside_and_boundary(self):
        polygon = ((0, 0), (10, 0), (10, 10), (0, 10))

        self.assertTrue(point_in_polygon((5, 5), polygon))
        self.assertTrue(point_in_polygon((0, 5), polygon))
        self.assertFalse(point_in_polygon((12, 5), polygon))

    def test_crossing_direction_reports_positive_and_negative_crossings(self):
        start = (0, 0)
        end = (10, 0)

        self.assertEqual(crossing_direction((5, -1), (5, 1), start, end), "positive")
        self.assertEqual(crossing_direction((5, 1), (5, -1), start, end), "negative")
        self.assertIsNone(crossing_direction((2, 1), (8, 1), start, end))


if __name__ == "__main__":
    unittest.main()
