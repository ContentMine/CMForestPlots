import unittest

from forestplots.helpers import forgiving_float

class ForgivingFloatTests(unittest.TestCase):

    def test_forgiving_float(self):

        valid_cases = [("1.23", 1.23),
                       ("1,23", 1.23),
                       ("-1.23", -1.23),
                       ("-1,23", -1.23),
                       ("~1,23", -1.23)]
        for case in valid_cases:
            self.assertEqual(forgiving_float(case[0]), case[1])

    def test_forgiving_float_garbage(self):
        with self.assertRaises(ValueError):
            forgiving_float("hello")
