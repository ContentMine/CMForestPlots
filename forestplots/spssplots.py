"""Specific implementation of SPSS forest plot parser."""

import collections
import difflib
import os
import re
import subprocess

import cv2

from forestplots.plots import ForestPlot, InvalidForestPlot
from forestplots.helpers import forgiving_float, sanity_check_values
from forestplots.projections import Projections

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

HEADER_RE = re.compile(r"^.*\n\s*(M-?H|[1IT]V)[\s.,]*(Fixed|Random)[\s.,]*(\d+)%\s*C[ilI!].*", re.MULTILINE)

TABLE_LINE_PARSE_RE = re.compile(r'^(.*?)\s+(\d+)\s+(\d+)\s+.*\s+([-—~]{0,1}\d+[.,:]\d*)\s*[/\[\({]([-—~]{0,1}\d+[.,:]\d*)\s*,\s*([-—~]{0,1}\d+[.,:]\d*)[\]}\)]\s*$')

SCALE_RE = re.compile(r'([-—~]{0,1}\d+[,.]*\d*)\s*([-—~]{0,1}\d+[,.]*\d*)\s*([-—~]{0,1}\d+[,.]*\d*)\s*([-—~]{0,1}\d+[,.]*\d*)\s*([-—~]{0,1}\d+[,.]*\d*)')
FAVOURS_RE = re.compile(r'Favours\s*[\[{\(](.*)[\]}\)]\s*Favours\s*[\[{\(](.*)[\]}\)]')

class SPSSForestPlot(ForestPlot):
    """Concrete subclass for processing SPSS forest plots."""

    def break_up_image(self):
        """Splits the forest plot image into sub-images required for OCR."""
        projections = Projections(os.path.join(self.image_directory, f"target_spss", "projections.xml"))

        # we want to split this into six areas, only four or which we currently use for OCR purposes
        x_line = int(projections.horizontal_lines[1].x1)
        y_top = int(projections.horizontal_lines[0].y)
        y_bottom = int(projections.horizontal_lines[1].y)

        image = cv2.imread(os.path.join(self.image_directory, "raw.png"))

        y_max, x_max = image.shape[0:2]

        raw_header_graphheads = image[0:y_top, x_line:x_max]
        cv2.imwrite(os.path.join(self.image_directory, "raw.header.graphheads.png"), raw_header_graphheads)

        raw_body_table = image[y_top:y_bottom, 0:x_line]
        cv2.imwrite(os.path.join(self.image_directory, "raw.body.table.png"), raw_body_table)

        # this will clip, so we add a little margin for error
        raw_footer_summary = image[y_bottom - 10:y_max, 0:x_line]
        cv2.imwrite(os.path.join(self.image_directory, "raw.footer.summary.png"), raw_footer_summary)

        raw_footer_scale = image[y_bottom:y_max, x_line:x_max]
        cv2.imwrite(os.path.join(self.image_directory, "raw.footer.scale.png"), raw_footer_scale)

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
            output_ocr_name = os.path.join(self.image_directory, f"footer.summary.{threshold}.txt")
            if not os.path.isfile(output_ocr_name):
                output_image_name = os.path.join(self.image_directory, f"footer.summary.{threshold}.png")
                if not os.path.isfile(output_image_name):
                    subprocess.run(["convert", "-black-threshold", f"{threshold}%", footer_image_path,
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
            groups[0] = groups[0].replace('1', 'I').replace('T', 'I').replace('MH', 'M-H')
            return tuple(groups)
        except AttributeError:
            raise ValueError

    def _process_header(self):
        header_image_path = os.path.join(self.image_directory, "raw.header.graphheads.png")
        if not os.path.isfile(header_image_path):
            raise InvalidForestPlot

        for threshold in range(50, 80, 2):
            output_ocr_name = os.path.join(self.image_directory, f"header.graphheads.{threshold}.txt")
            if not os.path.isfile(output_ocr_name):
                output_image_name = os.path.join(self.image_directory, f"header.graphheads.{threshold}.png")
                if not os.path.isfile(output_image_name):
                    subprocess.run(["convert", "-black-threshold", f"{threshold}%",
                                    header_image_path, output_image_name])
                # we could use -c preserve_interword_spaces=1
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
    def _decode_table_lines_ocr(ocr_prose):

        titles = []
        values = []

        for line in ocr_prose:

            # Fix some common number replacements in OCR
            line = line.replace('§', '5').replace('£', '[-')

            matches = TABLE_LINE_PARSE_RE.match(line)
            if not matches:
                continue
            groups = matches.groups()
            title = groups[0]
            try:
                value = (forgiving_float(groups[-3]), forgiving_float(groups[-2]), forgiving_float(groups[-1]))
                value = sanity_check_values(value)

                titles.append(title.replace("Cl", "CI"))
                values.append(value)
            except AttributeError:
                continue

        return titles, values

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

            ocr_prose = open(output_ocr_name, 'r').read()
            lines = [x.strip() for x in ocr_prose.split('\n') if x.strip()]

            # In general tesseract will end up converting this in one of two forms:
            # 1: it'll pull each column out one after another, and then make one single column from it all (this seems
            #    to be the most common).
            # 2: It'll actuall not parse the columns, and will preserve the tough layout of the table.
            # Given that, we need to try to parse both.

            hor_titles, hor_values = self._decode_table_lines_ocr(lines)

            ver_titles = []
            for line in lines:
                if line.startswith('Total'):
                    ver_titles.append(line.replace("Cl", "CI"))
                    break
                ver_titles.append(line)
            ver_values = self._decode_table_values_ocr(ocr_prose)
            if len(ver_titles) != len(ver_values):
                ver_titles = []

            values, titles = hor_values, hor_titles
            if len(ver_titles) > len(hor_titles):
                values, titles = ver_values, ver_titles

            if values:
                data = collections.OrderedDict(zip(titles, values))
                flattened_data = [(title, values[0], values[1], values[2]) for title, values in data.items()]
                self.primary_table.add_data(flattened_data)

    @staticmethod
    def _decode_footer_scale_ocr(ocr_prose):
        groups = None
        mid_scale = None

        lines = ocr_prose.split('\n')
        for line in lines:
            match = FAVOURS_RE.match(line)
            if match:
                groups = match.groups()
                continue
            match = SCALE_RE.match(line)
            if match:
                try:
                    mid_scale = forgiving_float(match.groups()[2])
                    continue
                except AttributeError:
                    pass

        if not groups or mid_scale is None:
            raise ValueError

        return groups, mid_scale

    def _process_scale(self):
        header_image_path = os.path.join(self.image_directory, "raw.footer.scale.png")
        if not os.path.isfile(header_image_path):
            raise InvalidForestPlot

        for threshold in range(50, 80, 2):
            output_ocr_name = os.path.join(self.image_directory, f"footer.scale.{threshold}.txt")
            if not os.path.isfile(output_ocr_name):
                output_image_name = os.path.join(self.image_directory, f"footer.scale.{threshold}.png")
                if not os.path.isfile(output_image_name):
                    subprocess.run(["convert", "-black-threshold", f"{threshold}%",
                                    header_image_path, output_image_name])
                # we could use -c preserve_interword_spaces=1
                subprocess.run(["tesseract", output_image_name, os.path.splitext(output_ocr_name)[0]],
                               capture_output=True)

            ocr_prose = open(output_ocr_name).read()
            try:
                groups, self.mid_point = SPSSForestPlot._decode_footer_scale_ocr(ocr_prose)
                self.group_a = groups[0]
                self.group_b = groups[1]
                break
            except ValueError:
                continue

    def _write_data_to_worksheet(self, worksheet):

        count = 1
        for key, value in self.summary.items():
            worksheet.cell(row=count, column=1, value=key)
            worksheet.cell(row=count, column=2, value=value)
            count = count + 1
        count = count + 1

        worksheet.cell(row=count, column=1, value="Hetrogeneity:")
        for key, value in self.hetrogeneity.items():
            worksheet.cell(row=count, column=2, value=key)
            worksheet.cell(row=count, column=3, value=value)
            count = count + 1
        count = count + 1

        worksheet.cell(row=count, column=1, value="Overall Effect:")
        for key, value in self.overall_effect.items():
            worksheet.cell(row=count, column=2, value=key)
            worksheet.cell(row=count, column=3, value=value)
            count = count + 1
        count = count + 1

        worksheet.cell(row=count, column=1, value="Data:")
        if self.primary_table.table_data:
            mode_table = self.primary_table.collapse_data()
            for value in mode_table:
                worksheet.cell(row=count, column=2, value=value[0])
                worksheet.cell(row=count, column=3, value=value[1])
                worksheet.cell(row=count, column=4, value=value[2])
                worksheet.cell(row=count, column=5, value=value[3])
                count += 1

    def process(self):
        """Process the possible SPSS forest plot."""
        self._process_footer()
        if not self.hetrogeneity or not self.overall_effect:
            raise InvalidForestPlot

        self._process_header()
        if not self.summary:
            print(f"ooo {self.image_directory}")
            raise InvalidForestPlot

        self._process_table()
        if not self.primary_table.table_data:
            raise InvalidForestPlot

        self._process_scale()
        try:
            if not self.group_a or not self.group_b or self.mid_point is None:
                raise InvalidForestPlot
        except AttributeError:
            raise InvalidForestPlot

    def json_repr(self):
        """Creates a JSON compatible dictionary representation."""

        res = {}

        for key, value in self.summary.items():
            res[key] = value

        for key, value in self.overall_effect.items():
            res[key] = value

        return res
