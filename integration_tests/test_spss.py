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
            count = 5

            self.assertEqual(worksheet.cell(row=count, column=1).value, "Hetrogeneity:")
            hetrogeneity = {}
            while True:
                key = worksheet.cell(row=count, column=2).value
                value = worksheet.cell(row=count, column=3).value
                count = count + 1
                if not key:
                    break
                else:
                    hetrogeneity[key] = float(value)

            self.assertEqual(worksheet.cell(row=count, column=1).value, "Overall Effect:")
            overall_effect = {}
            while True:
                key = worksheet.cell(row=count, column=2).value
                value = worksheet.cell(row=count, column=3).value
                count = count + 1
                if not key:
                    break
                else:
                    overall_effect[key] = float(value)

            self.assertEqual(worksheet.cell(row=count, column=1).value, "Data:")
            data = []
            while True:
                key = worksheet.cell(row=count, column=2).value
                value1 = worksheet.cell(row=count, column=3).value
                value2 = worksheet.cell(row=count, column=4).value
                value3 = worksheet.cell(row=count, column=5).value
                count = count + 1
                if not key:
                    count = count + 1
                    break
                else:
                    data.append((key, float(value1), float(value2), float(value3)))


            if result.find("image.4.3.96") != -1:
                self.assertEqual(estimator_type, "M-H")
                self.assertEqual(model_type, "Fixed")
                self.assertEqual(confidence_interval, "95")
                self.assertEqual(hetrogeneity, {
                    "Chi": 14.61,
                    "df": 9.0,
                    "P": 0.1,
                    "I": 38,
                })
                self.assertEqual(overall_effect, {
                    "Z": 2.7,
                    "P": 0.007,
                })
                expected_data = [
                    ("Suk 1995", 1.7, 0.49, 5.9),
                    ("Kuklo 2007", 0.4, 0.17, 0.95),
                    ("Karatoprak 2008", 0.37, 0.04, 3.79),
                    ("Helgeson 2010", 3.82, 0.82, 17.83),
                    ("Yilmaz 2012", 0.49, 0.04, 5.61),
                    ("Hwang 2012", 0.63, 0.3, 1.32),
                    ("Yang 2012", 1.00, 0.06, 17.12),
                    ("Halanski 2013", 0.94, 0.18, 4.96),
                    ("Samdani 2013", 0.25, 0.12, 0.55),
                    ("Sugarman 2013", 0.77, 0.25, 2.32),
                    ("Total (95% CI)", 0.61, 0.42, 0.87),
                ]
                self.assertEqual(len(expected_data), len(data))
                for expected, actual in zip(expected_data, data):
                    self.assertEqual(expected, actual)

            elif result.find("image.5.1.110") != -1:
                self.assertEqual(estimator_type, "M-H")
                self.assertEqual(model_type, "Fixed")
                self.assertEqual(confidence_interval, "95")
                self.assertEqual(hetrogeneity, {
                    "Chi": 2.11,
                    "df": 5.0,
                    "P": 0.83,
                    "I": 0.0,
                })
                self.assertEqual(overall_effect, {
                    "Z": 3.8,
                    "P": 0.0001,
                })

            elif result.find("image.6.1.96") != -1:
                self.assertEqual(estimator_type, "IV")
                self.assertEqual(model_type, "Fixed")
                self.assertEqual(confidence_interval, "95")
                self.assertEqual(hetrogeneity, {
                    "Chi": 15.08,
                    "df": 10.0,
                    "P": 0.13,
                    "I": 34.0,
                })
                self.assertEqual(overall_effect, {
                    "Z": 9.01,
                    "P": 0.00001,
                })

            elif result.find("image.6.2.96") != -1:
                self.assertEqual(estimator_type, "IV")
                self.assertEqual(model_type, "Random")
                self.assertEqual(confidence_interval, "95")
                self.assertEqual(hetrogeneity, {
                    "Tau": 5.98,
                    "Chi": 20.24,
                    "df": 8.0,
                    "P": 0.009,
                    "I": 60.0,
                })
                self.assertEqual(overall_effect, {
                    "Z": 5.43,
                    "P": 0.00001,
                })

            elif result.find("image.7.1.110") != -1:
                self.assertEqual(estimator_type, "IV")
                self.assertEqual(model_type, "Fixed")
                self.assertEqual(confidence_interval, "95")
                self.assertEqual(hetrogeneity, {
                    "Chi": 3.08,
                    "df": 4.0,
                    "P": 0.54,
                    "I": 0.0,
                })
                self.assertEqual(overall_effect, {
                    "Z": 0.54,
                    "P": 0.59,
                })
