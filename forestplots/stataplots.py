"""Specific implementation of Stata forest plot parser."""

import collections
import os
import re
import subprocess

import cv2

from forestplots.plots import ForestPlot, InvalidForestPlot, TABLE_VALUE_GROK_RE
from forestplots.helpers import forgiving_float, sanity_check_values
from forestplots.projections import Projections

HEADER_RE = re.compile(r".*(OR|RR|SMD|WMD|ES)\s*[\(\[](\d+)%.*")
TABLE_LINE_PARSE_RE = re.compile(r"\s*(.*?)[\s—]*([-~]{0,1}\d+[\.,:]?\d*)\s*[/\[\({]([-—~]{0,1}\d+[\.,:]?\d*)\s*,\s*([-—~]{0,1}\d+[\.,:]?\d*)[\]}\)]\s*([-—~]{0,1}\d+[\.,:]?\d*)")
OVERALL_LINE_RE = re.compile(r"(Overall|Subtotal) [\({\[].*squared\s*=\s*(\d+[\.,:]?\d*|[\.,])%[.,]\s*p\s*=\s*(\d+[\.,:]?\d*|[\.,])[\)}\]]")

VALUES_PARSE_RE = re.compile(r"\s*([-—~]{0,1}\d+[\.,:]?\d*)\s*[/\[\({]([-—~]{0,1}\d+[\.,:]?\d*)\s*,\s*([-—~]{0,1}\d+[\.,:]?\d*)[\]}\)]\s*([-—~]{0,1}\d+[\.,:]?\d*)")
SCALE_RE = re.compile(r'([-—~]{0,1}\d+[,.]*\d*)\s+([-—~]{0,1}\d+[,.]*\d*)\s+([-—~]{0,1}\d+[,.]*\d*)')


class StataForestPlot(ForestPlot):
    """Concrete subclass for processing Stata forest plots."""

    def break_up_image(self):
        """Splits the forest plot image into sub-images required for OCR."""
        projections = self.projections

        # we want to split this into three areas, only four or which we currently use for OCR purposes
        x_left = int(projections.vertical_lines[0].x)
        x_right = int(projections.vertical_lines[-1].x)
        y_top = int(projections.vertical_lines[0].y1)
        y_bottom = int(projections.horizontal_lines[-1].y)

        if x_left > x_right:
            x_left, x_right = x_right, x_left

        image = cv2.imread(os.path.join(self.image_directory, "raw.png"))

        y_max, x_max = image.shape[0:2]

        subimage = image[0:y_top, 0:x_max]
        cv2.imwrite(os.path.join(self.image_directory, "raw.header.png"), subimage)

        subimage = image[y_top:y_bottom, 0:x_left]
        cv2.imwrite(os.path.join(self.image_directory, "raw.titles.png"), subimage)

        subimage = image[y_top:y_bottom, x_right:x_max]
        cv2.imwrite(os.path.join(self.image_directory, "raw.values.png"), subimage)

        subimage = image[y_bottom:y_max, 0:x_max]
        cv2.imwrite(os.path.join(self.image_directory, "raw.scale.png"), subimage)


    @staticmethod
    def _decode_header_ocr(ocr_prose):
        lines = [x.strip() for x in ocr_prose.split('\n') if x.strip()]
        for line in lines:
            match = HEADER_RE.match(line)
            try:
                return tuple(match.groups())
            except AttributeError:
                pass
        raise ValueError

    def _process_header(self):
        header_image_path = os.path.join(self.image_directory, "raw.header.png")
        if not os.path.isfile(header_image_path):
            raise InvalidForestPlot

        for threshold in range(50, 80, 2):
            output_ocr_name = os.path.join(self.image_directory, "header.{0}.txt".format(threshold))
            if not os.path.isfile(output_ocr_name):
                output_image_name = os.path.join(self.image_directory, "header.{0}.png".format(threshold))
                if not os.path.isfile(output_image_name):
                    subprocess.run(["convert", "-black-threshold", "{0}%".format(threshold),
                                    header_image_path, output_image_name])
                subprocess.run(["tesseract", output_image_name, os.path.splitext(output_ocr_name)[0]],
                               capture_output=True)

            ocr_prose = open(output_ocr_name).read()
            try:
                estimator_type, confidence_interval = StataForestPlot._decode_header_ocr(ocr_prose)
                self.add_summary_information(estimator_type=estimator_type, model_type=None,
                                             confidence_interval=confidence_interval)
                break
            except ValueError:
                continue


    @staticmethod
    def _decode_values_ocr(ocr_prose):

        # Fix some common number replacements in OCR
        ocr_prose = ocr_prose.replace('§', '5').replace('$', '5').replace('£', '[-')
        lines = [x.strip() for x in ocr_prose.split('\n') if x.strip()]

        values = []
        weights = []

        # first find the values
        for line in lines:
            parts = TABLE_VALUE_GROK_RE.split(line)
            if len(parts) == 5:
                try:
                    value = (forgiving_float(parts[1]), forgiving_float(parts[2]), forgiving_float(parts[3]))
                    value = sanity_check_values(value)
                    values.append(value)
                except ValueError:
                    if parts == "(Excluded)":
                        values.append(("Excluded", "Excluded", "Excluded"))
                try:
                    weight = forgiving_float(parts[4].strip())
                    weights.append(weight)
                except ValueError:
                    pass
            else:
                try:
                    weight = forgiving_float(line)
                    weights.append(weight)
                except ValueError:
                    pass

        if len(values) != len(weights):
            raise ValueError

        res = []
        for value, weight in zip(values, weights):
            res.append((value[0], value[1], value[2], weight))

        return res

    def _process_values(self):
        values_image_path = os.path.join(self.image_directory, "raw.values.png")
        if not os.path.isfile(values_image_path):
            raise InvalidForestPlot

        total_values = {}

        for threshold in range(50, 80, 2):
            output_ocr_name = os.path.join(self.image_directory, "values.{0}.txt".format(threshold))
            if not os.path.isfile(output_ocr_name):
                output_image_name = os.path.join(self.image_directory, "values.{0}.png".format(threshold))
                if not os.path.isfile(output_image_name):
                    subprocess.run(["convert", "-black-threshold", "{0}%".format(threshold),
                                    values_image_path, output_image_name])
                subprocess.run(["tesseract", output_image_name, os.path.splitext(output_ocr_name)[0]],
                               capture_output=True)

            ocr_prose = open(output_ocr_name, 'r').read()
            try:
                values = self._decode_values_ocr(ocr_prose)
                if not total_values:
                    total_values[threshold] = values
                else:
                    current_len = len(total_values[next(iter(total_values))])
                    if current_len == len(values):
                        total_values[threshold] = values
                    elif len(values) > current_len:
                        total_values = {threshold: values}
            except ValueError:
                continue

        return total_values

    @staticmethod
    def _decode_table_titles_ocr(ocr_prose):

        titles = []
        lines = [x.strip() for x in ocr_prose.split('\n') if x.strip()]

        for line in lines:
            match = OVERALL_LINE_RE.match(line)
            if not match:
                titles.append(line)
                continue
            title, i_squared_str, probability_str = match.groups()
            titles.append((title, i_squared_str, probability_str))
            if title == "Overall":
                return titles

        raise ValueError

    def _process_titles(self):

        titles_image_path = os.path.join(self.image_directory, "raw.titles.png")
        if not os.path.isfile(titles_image_path):
            raise InvalidForestPlot

        total_titles = {}
        for threshold in range(50, 80, 2):
            output_ocr_name = os.path.join(self.image_directory, "titles.{0}.txt".format(threshold))
            if not os.path.isfile(output_ocr_name):
                output_image_name = os.path.join(self.image_directory, "titles.{0}.png".format(threshold))
                if not os.path.isfile(output_image_name):
                    subprocess.run(["convert", "-black-threshold", "{0}%".format(threshold),
                                    titles_image_path, output_image_name])
                subprocess.run(["tesseract", output_image_name, os.path.splitext(output_ocr_name)[0]],
                               capture_output=True)

            ocr_prose = open(output_ocr_name, 'r').read()
            try:
                titles = self._decode_table_titles_ocr(ocr_prose)
                total_titles[threshold] = titles
            except ValueError:
                pass

        return total_titles

    def _process_body(self):

        values_collection = self._process_values()
        titles_collection = self._process_titles()

        if not values_collection or not titles_collection:
            raise InvalidForestPlot

        values_count = len(values_collection[next(iter(values_collection))])

        # match the titles and value thresholds. Not sure this is necessary, but for now it simplifies things a little
        for threshold in range(50, 80, 2):
            if threshold in values_collection.keys() and threshold not in titles_collection.keys():
                del(values_collection[threshold])
            if threshold not in values_collection.keys() and threshold in titles_collection.keys():
                del(titles_collection[threshold])

        # work out how many groups we think there are, sanity checking against how many values we have
        group_counts = {threshold: len([x for x in titles_collection[threshold] if isinstance(x, tuple)]) for threshold in titles_collection}

        # further sanity check vs values
        clean_group_counts = {k: group_counts[k] for k in group_counts if len(titles_collection[k]) == values_count + (group_counts[k] - 1)}
        if not clean_group_counts:
            raise InvalidForestPlot
        raw_group_counts = list(clean_group_counts.values())
        most_common_groups = max(set(raw_group_counts), key=raw_group_counts.count)

        for threshold in clean_group_counts:
            if clean_group_counts[threshold] != most_common_groups:
                continue

            values = values_collection[threshold]
            titles = titles_collection[threshold]

            count = 0
            while count < most_common_groups:
                table = self.get_table(count)
                count += 1

                if count != most_common_groups:
                    table.add_title(titles[0])
                    titles = titles[1:]

                sub_titles = []
                sub_values = []

                while titles:
                    title = titles[0]
                    sub_titles.append(title)
                    if len(titles) > 1:
                        titles = titles[1:]
                    sub_values.append(values[0])
                    if len(values) > 1:
                        values = values[1:]

                    if isinstance(title, tuple):
                        break

                overall_title, i_squared_str, probability_str = sub_titles[-1]
                sub_titles[-1] = overall_title

                data = collections.OrderedDict(zip(sub_titles, sub_values))
                flattened_data = [(title, values[0], values[1], values[2], values[3]) for title, values in data.items()]
                table.add_data(flattened_data)
                table.metadata["i^2"] = i_squared_str
                try:
                    table.metadata["i^2"] = forgiving_float(i_squared_str)
                except ValueError:
                    pass
                table.metadata["p"] = probability_str
                try:
                    table.metadata["p"] = forgiving_float(probability_str)
                except ValueError:
                    pass


    def _write_data_to_worksheet(self, worksheet):
        count = 1
        for key, value in self.summary.items():
            worksheet.cell(row=count, column=1, value=key)
            worksheet.cell(row=count, column=2, value=value)
            count = count + 1
        count = count + 1

        worksheet.cell(row=count, column=1, value="Overall Effect:")
        for key, value in self.overall_effect.items():
            worksheet.cell(row=count, column=2, value=key)
            worksheet.cell(row=count, column=3, value=value)
            count = count + 1
        count = count + 1

        for table in self.table_list:
            title = table.collapse_titles()
            worksheet.cell(row=count, column=1, value="{0}:".format(title))
            mode_table = table.collapse_data()
            for value in mode_table:
                worksheet.cell(row=count, column=2, value=value[0])
                worksheet.cell(row=count, column=3, value=value[1])
                worksheet.cell(row=count, column=4, value=value[2])
                worksheet.cell(row=count, column=5, value=value[3])
                worksheet.cell(row=count, column=6, value=value[4])
                count += 1
            for key, value in table.metadata.items():
                worksheet.cell(row=count, column=2, value=key)
                worksheet.cell(row=count, column=3, value=value)
                count = count + 1
            count = count + 1

    @staticmethod
    def _decode_footer_scale_ocr(ocr_prose):

        ocr_prose = ocr_prose.replace('§', '5').replace('$', '5').replace('£', '[-')
        lines = [x.strip() for x in ocr_prose.split('\n') if x.strip()]
        for line in lines:
            match = SCALE_RE.match(line)
            try:
                return forgiving_float(match.groups()[1])
            except (ValueError, AttributeError):
                pass
        raise ValueError

    def _process_scale(self):
        header_image_path = os.path.join(self.image_directory, "raw.scale.png")
        if not os.path.isfile(header_image_path):
            raise InvalidForestPlot

        for threshold in range(50, 80, 2):
            output_ocr_name = os.path.join(self.image_directory, "scale.{0}.txt".format(threshold))
            if not os.path.isfile(output_ocr_name):
                output_image_name = os.path.join(self.image_directory, "scale.{0}.png".format(threshold))
                if not os.path.isfile(output_image_name):
                    subprocess.run(["convert", "-black-threshold", "{0}%".format(threshold),
                                    header_image_path, output_image_name])
                subprocess.run(["tesseract", output_image_name, os.path.splitext(output_ocr_name)[0]],
                               capture_output=True)

            ocr_prose = open(output_ocr_name).read()
            try:
                self.mid_point = StataForestPlot._decode_footer_scale_ocr(ocr_prose)
                break
            except ValueError:
                continue


    def process(self):
        """Process the possible Stata forest plot."""
        self._process_header()
        if not self.summary:
            raise InvalidForestPlot

        self._process_scale()

        self._process_body()

    def json_repr(self):
        repr = {}

        for key, value in self.summary.items():
            repr[key] = value

        for key, value in self.overall_effect.items():
            repr[key] = value

        return repr

