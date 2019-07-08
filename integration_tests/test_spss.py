import json
import os
import shutil
import tempfile
import unittest

import pytest
import openpyxl

import sys
sys.path.append(os.path.join(sys.path[0], ".."))

from forestplots import SPSSForestPlot
from forestplots import Controller

class FakeTempdir():
    def __init__(self, name):
        self.name = name


class IntegrationTests(unittest.TestCase):

    def setUp(self):
        self.tempdir = FakeTempdir("/tmp/testproject2") #tempfile.TemporaryDirectory()

    def tearDown(self):
        pass #self.tempdir.cleanup()

    def test_simple_spss(self):
        destination = shutil.copy("integration_tests/testdata/pmc5502154.pdf", self.tempdir.name)
        self.assertTrue(os.path.isfile(destination))

        c = Controller(self.tempdir.name)
        c.main()

        raw = open(os.path.join(self.tempdir.name, "forestplots.json")).read()
        data = json.loads(raw)

        # This paper has 5 forest plots
        self.assertEqual(len(data), 5)

        for result in data:
            workbook = openpyxl.load_workbook(result)
            worksheet = workbook.active

            estimator_type = worksheet.cell(row=1, column=2).value
            model_type = worksheet.cell(row=2, column=2).value
            confidence_interval = worksheet.cell(row=3, column=2).value

            if result.find("image.4.3.96") != -1:
                self.assertEqual(estimator_type, "M-H")
                self.assertEqual(model_type, "Fixed")
                self.assertEqual(confidence_interval, "95")

            elif result.find("image.5.1.110") != -1:
                self.assertEqual(estimator_type, "M-H")
                self.assertEqual(model_type, "Fixed")
                self.assertEqual(confidence_interval, "95")

            elif result.find("image.6.1.96") != -1:
                self.assertEqual(estimator_type, "IV")
                self.assertEqual(model_type, "Fixed")
                self.assertEqual(confidence_interval, "95")

            elif result.find("image.6.2.96") != -1:
                self.assertEqual(estimator_type, "IV")
                self.assertEqual(model_type, "Random")
                self.assertEqual(confidence_interval, "95")

            elif result.find("image.7.1.110") != -1:
                self.assertEqual(estimator_type, "IV")
                self.assertEqual(model_type, "Fixed")
                self.assertEqual(confidence_interval, "95")
