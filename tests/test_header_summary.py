import unittest

from forestplots import SPSSForestPlot

class DecodeExampleSPSSForestPlotHeaderSummary(unittest.TestCase):

    def test_example_1(self):
        example = 'Odds Ratio\nM-H. Fixed. 95% Cl\n\x0c'
        values = SPSSForestPlot._decode_header_summary_ocr(example)
        self.assertEqual(values, ("M-H", "Fixed", "95"))

    def test_example_2(self):
        example = 'Mean Difference\nIV. Random. 95% Cl\n\x0c'
        values = SPSSForestPlot._decode_header_summary_ocr(example)
        self.assertEqual(values, ("IV", "Random", "95"))

    def test_example_3(self):
        example = 'Mean Difference\n1V. Fixed, 95% Cl\n'
        values = SPSSForestPlot._decode_header_summary_ocr(example)
        self.assertEqual(values, ("IV", "Fixed", "95"))
