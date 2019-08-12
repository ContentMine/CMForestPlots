import unittest

from forestplots import SPSSForestPlot

class DecodeExampleSPSSForestPlotFooterScale(unittest.TestCase):

    def test_example_1(self):
        example = """
enema nore gaomeenenenreennreneena genera aaa
0.01 0.4 1 10 100
Favours [Pedicle screw] Favours [Hybrid Instrumentation]
"""
        groups, mid_scale = SPSSForestPlot._decode_footer_scale_ocr(example)
        self.assertEqual(groups, ("Pedicle screw", "Hybrid Instrumentation"))
        self.assertEqual(mid_scale, 1.0)

    def test_example_2(self):
        example = """
NN EE —
-10 5 0 5 10

Favours [Pedicle screw] Favours [Hybrid Instrumentation}
"""
        groups, mid_scale = SPSSForestPlot._decode_footer_scale_ocr(example)
        self.assertEqual(groups, ("Pedicle screw", "Hybrid Instrumentation"))
        self.assertEqual(mid_scale, 0.0)

    def test_example_3(self):
        example = """
NN EE —
-10 5 0 5 10

Favours [Pedicle Screw] Favours [Hybrid Instrumentation]
"""
        groups, mid_scale = SPSSForestPlot._decode_footer_scale_ocr(example)
        self.assertEqual(groups, ("Pedicle Screw", "Hybrid Instrumentation"))
        self.assertEqual(mid_scale, 0.0)
