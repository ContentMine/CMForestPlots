import unittest

from forestplots import SPSSForestPlot, StataForestPlot, ForestPlot

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
        values = ForestPlot._decode_table_values_ocr(example)
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
        values = ForestPlot._decode_table_values_ocr(example)
        self.assertEqual(values, [
            (-4.0, -7.34, -0.66),
            (-9.0, -13.58, -4.42),
            (-4.40, -9.41, 0.64),
        ])

    def test_value_example_3(self):
        example = """
        29 5.5% -1.00/-6.17, 4.17] 2006
30 18.8% -1.00[-3.79, 1.79] 2008
177 155% 2.50 [-0.58, 5.58] 2010
71 49.8% 0.23 [-1.49, 1.95] 2012
21 10.4% 0.70 [-3.06, 4.46] 2014



328 100.0% 0.33 [-0.88, 1.54]
"""
        values = ForestPlot._decode_table_values_ocr(example)
        self.assertEqual(values, [
            (-1.00, -6.17, 4.17),
            (-1.00, -3.79, 1.79),
            (2.50, -0.58, 5.58),
            (0.23, -1.49, 1.95),
            (0.70, -3.06, 4.46),
            (0.33, -0.88, 1.54),
        ])


    def test_value_example_4(self):
        example = """
1.57 (0.79, 3.12]
2.88 (1.50, §.56]
1.07 (0.62, 1.84]
"""
        values = ForestPlot._decode_table_values_ocr(example)
        self.assertEqual(values, [
            (1.57, 0.79, 3.12),
            (2.88, 1.5, 5.56),
            (1.07, 0.62, 1.84),
        ])

    def test_value_example_5(self):
        example = """
1.00 £6.17, 4.17] 2008
"""
        values = ForestPlot._decode_table_values_ocr(example)
        self.assertEqual(values, [
            (1.0, -6.17, 4.17),
        ])

    def test_value_example_6(self):
        example = """6.04 (0.34, 106.22)

-_———e—_—— 216.7 (1.23, 380.41)

——_+—_—_.

<>

14,82 (0.86, 256.77)
"""
        values = ForestPlot._decode_table_values_ocr(example)
        self.assertEqual(values, [
            (6.04, 0.34, 106.22),
            (216.7, 1.23, 380.41),
            (14.82, 0.86, 256.77),
        ])


    def test_value_example_7(self):
        example = """6.04 (0 34, 106.22)

21.67 (1.23. 380.41)

14.82 (0.86, 256.77)

$1.33 (9.43, 279.57)

20.35 (5 64, 73.39)
"""
        values = ForestPlot._decode_table_values_ocr(example)
        self.assertEqual(values, [
            (6.04, 0.34, 106.22),
            (21.67, 1.23, 380.41),
            (14.82, 0.86, 256.77),
            (51.33, 9.43, 279.57),
            (20.35, 5.64, 73.39),
        ])

    def test_value_example_8(self):
        example = """5.06 (2.19, 11.69)
(Excluded)

2.57 (0.71, 9.31)"""
        values = ForestPlot._decode_table_values_ocr(example)
        self.assertEqual(values, [
            (5.06, 2.19, 11.69),
            ("Excluded", "Excluded", "Excluded"),
            (2.57, 0.71, 9.31),
        ])



class DecodeExampleSPSSForestPlotTableLines(unittest.TestCase):

    def test_lines_example_1(self):
        example = [
            "Chua D (2010) 15 47 9 48 8.9% 1.70 (0.83, 3.50)",
            "Dou-Dou Li (2015) 9 18 § 18 7.4% 1.80 (0.75, 4.32)",
            "Fei Teng (2017) 22 26 6 26 9.0% 3.53 (1.72, 7.22]",
        ]

        titles, values = SPSSForestPlot._decode_table_lines_ocr(example)
        self.assertEqual(titles, ["Chua D (2010)", "Dou-Dou Li (2015)", "Fei Teng (2017)"])
        self.assertEqual(values, [
            (1.7, 0.83, 3.5),
            (1.8, 0.75, 4.32),
            (3.53, 1.72, 7.22),
        ])




