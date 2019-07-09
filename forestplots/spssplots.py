"""Specific implementation of SPSS forest plot parser."""

import collections
import difflib
import os
import re
import subprocess

from forestplots.plots import ForestPlot, InvalidForestPlot
from forestplots.helpers import forgiving_float

TAU_LABEL = "Tau"
CHI_LABEL = "Chi"
DF_LABEL = "df"
P_LABEL = "P"
I_LABEL = "I"
Z_LABEL = "Z"

HETROGENEITY_KEYS = [TAU_LABEL, CHI_LABEL, DF_LABEL, P_LABEL, I_LABEL]
OVERALL_EFFECT_KEYS = [Z_LABEL, P_LABEL]

PARTS_SPLIT_RE = re.compile(r"([\w7\?]+.?\s*[=<>]\s*\d+[,.]*\d*)")
PARTS_GROK_RE = re.compile(r"([\w7\?]+.?)\s*[=<>]\s*(\d+[,.]*\d*)")

HEADER_RE = re.compile(r"^.*\n\s*(M-H|[1I]V)[\s.,]*(Fixed|Random)[\s.,]*(\d+)%\s*C[ilI!].*", re.MULTILINE)

TABLE_VALUE_SPLIT_RE = re.compile(r'([-~]{0,1}\d+[.,:]\d*\s*[/\[\({][-~]{0,1}\d+[.,:]\d*\s*,\s*[-~]{0,1}\d+[.,:]\d*[\]}\)])')
TABLE_VALUE_GROK_RE = re.compile(r'([-~]{0,1}\d+[.,:]\d*)\s*[/\[\({]([-~]{0,1}\d+[.,:]\d*)\s*,\s*([-~]{0,1}\d+[.,:]\d*)[\]}\)]')

class SPSSForestPlot(ForestPlot):
    """Concrete subclass for processing SPSS forest plots."""

    @staticmethod
    def _decode_footer_summary_ocr(ocr_prose):

        lines = [x.strip() for x in ocr_prose.split('\n') if x.strip()]

        hetrogeneity = collections.OrderedDict()
        overall_effect = collections.OrderedDict()

        for line in lines:
            prefix = ""
            offset_h = line.find("Heterogeneity:")
            offset_t = line.find("Test for overall effect:")
            offset = 0
            if offset_h != -1:
                prefix = "Heterogeneity:"
                offset = offset_h
            elif offset_t != -1:
                prefix = "Test for overall effect:"
                offset = offset_t
            else:
                continue
            data = line[len(prefix) + offset:].strip()
            parts = PARTS_SPLIT_RE.split(data)

            for part in parts:
                match = PARTS_GROK_RE.match(part)
                if not match:
                    continue
                key, value = match.groups()
                key = key.strip()

                if prefix == "Heterogeneity:":
                    if key in ("7", "?", "F"):
                        key = "I"
                    possible_keys = difflib.get_close_matches(key, HETROGENEITY_KEYS)
                    try:
                        hetrogeneity[possible_keys[0]] = forgiving_float(value)
                    except (IndexError, ValueError):
                        pass
                else:
                    possible_keys = difflib.get_close_matches(key, OVERALL_EFFECT_KEYS)
                    try:
                        overall_effect[possible_keys[0]] = forgiving_float(value)
                    except (IndexError, ValueError):
                        pass

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
        match = HEADER_RE.match(ocr_prose)
        try:
            groups = list(match.groups())
            groups[0] = groups[0].replace('1', 'I')
            return tuple(groups)
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

    @staticmethod
    def _decode_table_values_ocr(ocr_prose):

        # Fix some common number replacements in OCR
        ocr_prose = ocr_prose.replace('§', '5')

        parts = TABLE_VALUE_SPLIT_RE.split(ocr_prose)
        values = []
        for part in parts:
            try:
                groups = TABLE_VALUE_GROK_RE.match(part).groups()
                value = (forgiving_float(groups[0]), forgiving_float(groups[1]), forgiving_float(groups[2]))

                # We note that the leading - is often missed, but the ones within the block less so, so we
                # have a sanity check here and see if adding a -ve to the first value helps
                if not value[1] < value[0] < value[2]:
                    if value[1] < -value[0] < value[2]:
                        value = (-value[0], value[1], value[2])

                values.append(value)
            except AttributeError:
                pass
        return values


    def _process_table(self):
        image_path = os.path.join(self.image_directory, "raw.body.table.png")
        if not os.path.isfile(image_path):
            raise InvalidForestPlot

        for threshold in range(50, 80, 2):
            output_ocr_name = os.path.join(self.image_directory, "body.table.{0}.txt".format(threshold))
            if not os.path.isfile(output_ocr_name):
                output_image_name = os.path.join(self.image_directory, "body.table.{0}.png".format(threshold))
                if not os.path.isfile(output_image_name):
                    subprocess.run(["convert", "-black-threshold", "{0}%".format(threshold),
                                    image_path, output_image_name])
                subprocess.run(["tesseract", output_image_name, os.path.splitext(output_ocr_name)[0]],
                               capture_output=True)

            titles = []
            ocr_prose = open(output_ocr_name, 'r').read()
            lines = [x.strip() for x in ocr_prose.split('\n') if x.strip()]

            for line in lines:
                if line.startswith('Total'):
                    titles.append(line.replace("Cl", "CI"))
                    break
                titles.append(line)

            values = SPSSForestPlot._decode_table_values_ocr(ocr_prose)

            if values and len(values) == len(titles):
                data = collections.OrderedDict(zip(titles, values))
                flattened_data = [(title, values[0], values[1], values[2]) for title, values in data.items()]
                print(flattened_data[0])
                self.add_table_data(flattened_data)

    def process(self):
        """Process the possible SPSS forest plot."""
        self._process_footer()
        if not self.hetrogeneity or not self.overall_effect:
            raise InvalidForestPlot

        self._process_header()
        if not self.summary:
            raise InvalidForestPlot

        self._process_table()
        if not self.table_data:
            raise InvalidForestPlot
