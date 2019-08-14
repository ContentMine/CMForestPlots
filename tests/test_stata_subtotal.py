import unittest

from forestplots import SPSSForestPlot, StataForestPlot, ForestPlot, StataTableResults

class DecodeExampleStataSubtotalValues(unittest.TestCase):

    def test_example_1(self):
        example = """
van den Bos (2013)

Ding (2013)

Overall (I-squared = 31.0%, p = 0.203)

1.71 (1.24, 2.36)

1.35 (0.99, 1.84)

1.73 (1.48, 2.03)

23.91

28.98

100.00
"""
        plots = StataForestPlot._decode_table_columnwise_ocr(example)
        self.assertEqual(len(plots), 1)
        plot = plots[0]
        self.assertEqual(plot.i_squared, 31.0)
        self.assertEqual(plot.probability, 0.203)
        self.assertEqual(plot.titles, ["van den Bos (2013)", "Ding (2013)", "Overall"])
        self.assertEqual(len(plot.values), 3)
        self.assertEqual(len(plot.weights), 3)

    def test_example_2(self):
        example = """
Cereal

Tiger (2013)

Subtotal (I-squared = 21.4%, p = 0.1)

Skateboard

Hawk (2044)

Subtotal (I-squared = .%, p = .)

Overall (I-squared = 31.0%, p = 0.203)

1.71 (1.24, 2.36)

1.71 (1.24, 2.36)

1.35 (0.99, 1.84)

1.35 (0.99, 1.84)

1.73 (1.48, 2.03)

23.91

23.91

28.98

28.98

100.00
"""
        plots = StataForestPlot._decode_table_columnwise_ocr(example)
        self.assertEqual(len(plots), 3)

        plot = plots[0]
        self.assertEqual(plot.i_squared, 21.4)
        self.assertEqual(plot.probability, 0.1)
        self.assertEqual(plot.titles, ["Tiger (2013)", "Subtotal"])
        self.assertEqual(len(plot.values), 2)
        self.assertEqual(len(plot.weights), 2)

        plot = plots[1]
        self.assertEqual(plot.i_squared, ".")
        self.assertEqual(plot.probability, ".")
        self.assertEqual(plot.titles, ["Hawk (2044)", "Subtotal"])
        self.assertEqual(len(plot.values), 2)
        self.assertEqual(len(plot.weights), 2)

        plot = plots[2]
        self.assertEqual(plot.i_squared, 31.0)
        self.assertEqual(plot.probability, 0.203)
        self.assertEqual(plot.titles, ["Overall"])
        self.assertEqual(len(plot.values), 1)
        self.assertEqual(len(plot.weights), 1)
