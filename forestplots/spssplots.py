"""Specific implementation of SPSS forest plot parser."""

import collections
import difflib
import os
import re
import subprocess

from forestplots.plots import ForestPlot, InvalidForestPlot
from forestplots.helpers import forgiving_float

class SPSSForestPlot(ForestPlot):
    """Concrete subclass for processing SPSS forest plots."""

    TAU_LABEL = "Tau"
    CHI_LABEL = "Chi"
    DF_LABEL = "df"
    P_LABEL = "P"
    I_LABEL = "I"
    Z_LABEL = "Z"

    HETROGENEITY_KEYS = [TAU_LABEL, CHI_LABEL, DF_LABEL, P_LABEL, I_LABEL]
    OVERALL_EFFECT_KEYS = [Z_LABEL, P_LABEL]

    PARTS_SPLIT_RE = re.compile(r"([\w7]+.?\s*=\s*\d+[,.]*\d*)")
    PARTS_GROK_RE = re.compile(r"([\w7]+.?)\s*=\s*(\d+[,.]*\d*)")

    HEADER_RE = re.compile(r"^.*\n\s*(M-H|IV)[\s.,]*(Fixed|Random)[\s.,]*(\d+)%\s*C[ilI!].*", re.MULTILINE)

    @staticmethod
    def _decode_footer_summary_ocr(ocr_prose):

        lines = [x.strip() for x in ocr_prose.split('\n') if x.strip()]

        hetrogeneity = collections.OrderedDict()
        overall_effect = collections.OrderedDict()

        for line in lines:
            prefix = ""
            if line.startswith("Heterogeneity:"):
                prefix = "Heterogeneity:"
            elif line.startswith("Test for overall effect:"):
                prefix = "Test for overall effect:"
            else:
                continue
            data = line[len(prefix):].strip()
            parts = SPSSForestPlot.PARTS_SPLIT_RE.split(data)

            for part in parts:
                match = SPSSForestPlot.PARTS_GROK_RE.match(part)
                if not match:
                    continue
                key, value = match.groups()

                if prefix == "Heterogeneity:":
                    possible_keys = difflib.get_close_matches(key, SPSSForestPlot.HETROGENEITY_KEYS)
                    try:
                        hetrogeneity[possible_keys[0]] = forgiving_float(value)
                    except (IndexError, ValueError):
                        print("Failed to grok {0}".format(part))
                else:
                    possible_keys = difflib.get_close_matches(key, SPSSForestPlot.OVERALL_EFFECT_KEYS)
                    try:
                        overall_effect[possible_keys[0]] = forgiving_float(value)
                    except (IndexError, ValueError):
                        print("Failed to grok {0}".format(part))

        return hetrogeneity, overall_effect

    def _process_footer(self):
        footer_image_path = os.path.join(self.image_directory, "raw.footer.summary.png")
        if not os.path.isfile(footer_image_path):
            raise InvalidForestPlot

        for threshold in range(50, 80, 2):
            output_ocr_name = os.path.join(self.image_directory, "footer.summary.{0}.txt".format(threshold))
            if not os.path.isfile(output_ocr_name):
                output_image_name = os.path.join(self.image_directory, "footer.summary.{0}.png".format(threshold))
                if not os.path.isfile(output_image_name):
                    subprocess.run(["convert", "-black-threshold", "{0}%".format(threshold), footer_image_path,
                                    output_image_name])
                subprocess.run(["tesseract", output_image_name, os.path.splitext(output_ocr_name)[0]],
                               capture_output=True)

            ocr_prose = open(output_ocr_name).read()
            hetrogeneity, overall_effect = SPSSForestPlot._decode_footer_summary_ocr(ocr_prose)
            if len(hetrogeneity) > len(self.hetrogeneity):
                self.hetrogeneity = hetrogeneity
            if len(overall_effect) > len(self.overall_effect):
                self.overall_effect = overall_effect

    @staticmethod
    def _decode_header_summary_ocr(ocr_prose):
        print(ocr_prose)
        match = SPSSForestPlot.HEADER_RE.match(ocr_prose)
        try:
            return match.groups()
        except AttributeError:
            raise ValueError

    def _process_header(self):
        header_image_path = os.path.join(self.image_directory, "raw.header.graphheads.png")
        if not os.path.isfile(header_image_path):
            raise InvalidForestPlot

        for threshold in range(50, 80, 2):
            output_ocr_name = os.path.join(self.image_directory, "header.graphheads.{0}.txt".format(threshold))
            if not os.path.isfile(output_ocr_name):
                output_image_name = os.path.join(self.image_directory, "header.graphheads.{0}.png".format(threshold))
                if not os.path.isfile(output_image_name):
                    subprocess.run(["convert", "-black-threshold", "{0}%".format(threshold),
                                    header_image_path, output_image_name])
                subprocess.run(["tesseract", output_image_name, os.path.splitext(output_ocr_name)[0]],
                               capture_output=True)

            ocr_prose = open(output_ocr_name).read()
            try:
                estimator_type, model_type, confidence_interval = SPSSForestPlot._decode_header_summary_ocr(ocr_prose)
                self.add_summary_information(estimator_type=estimator_type, model_type=model_type,
                                             confidence_interval=confidence_interval)
                break
            except ValueError:
                continue


    def process(self):
        """Process the possible SPSS forest plot."""
        self._process_footer()
        if not self.hetrogeneity or not self.overall_effect:
            raise InvalidForestPlot

        self._process_header()
        if not self.summary:
            raise InvalidForestPlot
