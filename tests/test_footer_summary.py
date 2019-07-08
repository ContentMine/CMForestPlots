import unittest

from forestplots import SPSSForestPlot

class DecodeExampleSPSSForestPlotFooterSummary(unittest.TestCase):

    def test_example_1(self):
        example = 'Heterogeneity: Tau? = 0.00; Chi? = 2.98, df= 4 (P = 0.56), I= 0% |\nTest for overall effect: Z= 3.12'
        hetrogeneity, overall_effect = SPSSForestPlot._decode_footer_summary_ocr(example)
        self.assertEqual(dict(hetrogeneity), {"Tau": 0.00, "Chi": 2.98, "df": 4, "P": 0.56, "I": 0.0})
        self.assertEqual(overall_effect, {"Z": 3.12})

    def test_example_2(self):
        example = 'Heterogeneity: Chi? = 2.07, df= 10 (P= 1.00); /7= 0%\nTest for overall effect: Z= 1.13 (P = 0.26)\n\x0c'
        hetrogeneity, overall_effect = SPSSForestPlot._decode_footer_summary_ocr(example)
        self.assertEqual(dict(hetrogeneity), {"Chi": 2.07, "df": 10, "P": 1.00})
        self.assertEqual(overall_effect, {"Z": 1.13, "P": 0.26})

    def test_example_3(self):
        example = 'Heterogeneity: Ch? = 2.11, df = 5 (P = 0.83); I= 0%\nTest for overall effect: Z = 3.80 (P = 0.0001)\n\n \n\x0c'
        hetrogeneity, overall_effect = SPSSForestPlot._decode_footer_summary_ocr(example)
        self.assertEqual(dict(hetrogeneity), {"Chi": 2.11, "df": 5.0, "P": 0.83, "I": 0.00})
        self.assertEqual(overall_effect, {"Z": 3.80, "P": 0.0001})

    def test_example_4(self):
        example = 'Heterogeneity: Chi? = 15.08, df= 10 (P = 0.13);\n‘Test for overall effect: Z = 9.01 (P < 0.00001)\n\n\n\n'
        hetrogeneity, overall_effect = SPSSForestPlot._decode_footer_summary_ocr(example)
        self.assertEqual(dict(hetrogeneity), {"Chi": 15.08, "df": 10.0, "P": 0.13})
        self.assertEqual(overall_effect, {"Z": 9.01, "P": 0.00001})

    def test_example_5(self):
        example = 'Heterogeneity: Chi? = 15.08, df = 10 (P = 0.13); F = 34%\nTest for overall effect: Z = 9.01 (P < 0.00001)\n\n'
        hetrogeneity, overall_effect = SPSSForestPlot._decode_footer_summary_ocr(example)
        self.assertEqual(dict(hetrogeneity), {"Chi": 15.08, "df": 10.0, "P": 0.13})
        self.assertEqual(overall_effect, {"Z": 9.01, "P": 0.00001})

