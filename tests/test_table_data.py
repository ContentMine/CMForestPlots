import unittest

from forestplots import SPSSForestPlot

class DecodeExampleSPSSForestPlotTableValues(unittest.TestCase):

    def test_value_example_1(self):
        example = """
29 5.5% -1.00[-6.17, 4.17] 2006
30 18.8% -1.00[-3.79, 1.79] 2008
177 15.5% 2.50 [-0.58, 5.58] 2010
71 49.8% 0.23 [-1.49, 1.95] 2012
21 10.4% 0.70 [-3.08, 4.48] 2014



328 100.0% 0.33 [-0.88, 1.54]
"""
        values = SPSSForestPlot._decode_table_values_ocr(example)
        self.assertEqual(values, [
            (-1.00, -6.17, 4.17),
            (-1.00, -3.79, 1.79),
            (2.50, -0.58, 5.58),
            (0.23, -1.49, 1.95),
            (0.70, -3.08, 4.48),
            (0.33, -0.88, 1.54),
        ])

    def test_value_example_2(self):
        example = """
-4.00 [-7.34, -0.66]
9.00 [-13.58, ~4.42]
-4.40 [-9.41, 0.64]
"""
        values = SPSSForestPlot._decode_table_values_ocr(example)
        self.assertEqual(values, [
            (-4.0, -7.34, -0.66),
            (9.0, -13.58, -4.42),
            (-4.40, -9.41, 0.64),
        ])
