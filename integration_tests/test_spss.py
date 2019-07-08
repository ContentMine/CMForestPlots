import json
import os
import shutil
import tempfile
import unittest

import pytest

import sys
sys.path.append(os.path.join(sys.path[0], ".."))

from forestplots import SPSSForestPlot
from forestplots import Controller

class IntegrationTests(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tempdir.cleanup()

    def test_simple_spss(self):
        destination = shutil.copy("integration_tests/testdata/pmc5502154.pdf", self.tempdir.name)
        self.assertTrue(os.path.isfile(destination))

        c = Controller(self.tempdir.name)
        c.main()

        raw = open(os.path.join(self.tempdir.name, "forestplots.json")).read()
        data = json.loads(raw)

        # This paper has 5 forest plots
        self.assertEqual(len(data), 5)


