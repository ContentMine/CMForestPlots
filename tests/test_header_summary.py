import unittest

from forestplots import SPSSForestPlot, StataForestPlot

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

    def test_example_4(self):
        example = "Mean Difference\nTV. Random. 95% CI\n"
        values = SPSSForestPlot._decode_header_summary_ocr(example)
        self.assertEqual(values, ("IV", "Random", "95"))


class DecodeExampleStataForestPlotHeaderSummary(unittest.TestCase):

    def test_example_1(self):
        example = 'Study %\nID OR (95% Cl) Weight\n'
        values = StataForestPlot._decode_header_ocr(example)
        self.assertEqual(values, ("OR", "95"))

    def test_example_2(self):
        example = 'Study %\n10 OR (95% Cl) Weight\n'
        values = StataForestPlot._decode_header_ocr(example)
        self.assertEqual(values, ("OR", "95"))
