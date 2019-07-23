"""Specific implementation of Stata forest plot parser."""

import collections
import os
import re
import subprocess

from forestplots.plots import ForestPlot, InvalidForestPlot
from forestplots.helpers import forgiving_float, sanity_check_values

HEADER_RE = re.compile(r".*(OR)\s*[\(\[](\d+)%.*")
TABLE_LINE_PARSE_RE = re.compile(r"\s*(.*?)[\s—]*([-~]{0,1}\d+[.,:]?\d*)\s*[/\[\({]([-~]{0,1}\d+[.,:]?\d*)\s*,\s*([-~]{0,1}\d+[.,:]?\d*)[\]}\)]\s*([-~]{0,1}\d+[.,:]?\d*)")
OVERALL_LINE_RE = re.compile(r"Overall [\({\[].*squared = (\d+[.,:]?\d*)%[.,]\s*p\s*=\s*(\d+[.,:]?\d*)[\)}\]]")

class StataForestPlot(ForestPlot):
    """Concrete subclass for processing Stata forest plots."""

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
    def _decode_table_columnwise_ocr(ocr_prose):

        titles = []
        lines = [x.strip() for x in ocr_prose.split('\n') if x.strip()]

        for line in lines:

            # Fix some common number replacements in OCR
            line = line.replace('§', '5').replace('£', '[-')

            matches = OVERALL_LINE_RE.match(line)
            if not matches:
                titles.append(line)
            else:
                titles.append("Overall")
                break

        # having got the titles, now try to find the values
        values = ForestPlot._decode_table_values_ocr(ocr_prose)

        if len(titles) != len(values):
            raise ValueError

        # now see if we can extract the weights from the last n lines
        weights = [forgiving_float(x) for x in lines[-1 * len(titles):]]

        return titles, values, weights

    @staticmethod
    def _decode_table_lines_ocr(ocr_prose):

        titles = []
        values = []
        weights = []

        lines = [x.strip() for x in ocr_prose.split('\n') if x.strip()]
        for line in lines:

            # Fix some common number replacements in OCR
            line = line.replace('§', '5').replace('£', '[-')

            matches = TABLE_LINE_PARSE_RE.match(line)
            if not matches:
                continue
            groups = matches.groups()
            title = groups[0]
            try:
                value = (forgiving_float(groups[1]), forgiving_float(groups[2]), forgiving_float(groups[3]))
                value = sanity_check_values(value)

                if OVERALL_LINE_RE.match(title):
                    title = "Overall"

                titles.append(title)
                values.append(value)

                weight = forgiving_float(groups[-1])
                weights.append(weight)
            except AttributeError:
                continue

        return titles, values, weights

    def _process_body(self):
        print(self.image_directory)
        header_image_path = os.path.join(self.image_directory, "raw.body.png")
        if not os.path.isfile(header_image_path):
            raise InvalidForestPlot

        for threshold in range(50, 80, 2):
            output_ocr_name = os.path.join(self.image_directory, "body.{0}.txt".format(threshold))
            if not os.path.isfile(output_ocr_name):
                output_image_name = os.path.join(self.image_directory, "body.{0}.png".format(threshold))
                if not os.path.isfile(output_image_name):
                    subprocess.run(["convert", "-black-threshold", "{0}%".format(threshold),
                                    header_image_path, output_image_name])
                subprocess.run(["tesseract", output_image_name, os.path.splitext(output_ocr_name)[0]],
                               capture_output=True)

        # We need to work out first if we have sub graphs or not
        graph_counts = []
        for threshold in range(50, 80, 2):
            output_ocr_name = os.path.join(self.image_directory, "body.{0}.txt".format(threshold))

            ocr_prose = open(output_ocr_name, 'r').read()
            graph_counts.append(ocr_prose.count('Subtotal'))

        # Take the mode as to how many subgraphs there are
        graph_count = max(set(graph_counts), key=graph_counts.count)


        if graph_count in (0, 1):
            # treat as a single graph
            for threshold in range(50, 80, 2):
                output_ocr_name = os.path.join(self.image_directory, "body.{0}.txt".format(threshold))

                ocr_prose = open(output_ocr_name, 'r').read()

                horizontal_results = ([], [], [])
                vertical_results = ([], [], [])
                try:
                    horizontal_results = self._decode_table_lines_ocr(ocr_prose)
                except ValueError:
                    pass
                try:
                    vertical_results = self._decode_table_columnwise_ocr(ocr_prose)
                except ValueError:
                    pass

                results = horizontal_results
                if len(vertical_results[0]) > len(horizontal_results[0]):
                    results = vertical_results

                print(results)
                if results[0]:
                    data = collections.OrderedDict(zip(results[0], results[1]))
                    flattened_data = [(title, values[0], values[1], values[2]) for title, values in data.items()]
                    self.primary_table.add_data(flattened_data)
        else:
            # treat as multiple graphs, will add later
            raise InvalidForestPlot



        # depending on how tesseract feels, it'll have either kept the rows of the table intact or it'll
        # have read each column in turn, listing them one after another in the file




    def process(self):
        """Process the possible Stata forest plot."""
        self._process_header()
        if not self.summary:
            raise InvalidForestPlot

        self._process_body()
