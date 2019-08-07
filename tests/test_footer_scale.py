import unittest

from forestplots import SPSSForestPlot

class DecodeExampleSPSSForestPlotFooterScale(unittest.TestCase):

    def test_example_1(self):
        example = """
enema nore gaomeenenenreennreneena genera aaa
0.01 0.4 1 10 100
Favours [Pedicle screw] Favours [Hybrid Instrumentation]
"""
        group_a, group_b = SPSSForestPlot._decode_footer_scale_ocr(example)
        self.assertEqual(group_a, "Pedicle screw")
        self.assertEqual(group_b, "Hybrid Instrumentation")
