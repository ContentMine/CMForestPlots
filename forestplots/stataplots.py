"""Specific implementation of Stata forest plot parser."""

import collections
import os
import re
import subprocess

from forestplots.plots import ForestPlot, InvalidForestPlot
from forestplots.helpers import forgiving_float, sanity_check_values

StataTableResults = collections.namedtuple('StataTableResults', 'titles values weights i_squared probability title')

HEADER_RE = re.compile(r".*(OR)\s*[\(\[](\d+)%.*")
TABLE_LINE_PARSE_RE = re.compile(r"\s*(.*?)[\s—]*([-~]{0,1}\d+[.,:]?\d*)\s*[/\[\({]([-~]{0,1}\d+[.,:]?\d*)\s*,\s*([-~]{0,1}\d+[.,:]?\d*)[\]}\)]\s*([-~]{0,1}\d+[.,:]?\d*)")
OVERALL_LINE_RE = re.compile(r"(Overall|Subtotal) [\({\[].*squared = (\d+[.,:]?\d*)%[.,]\s*p\s*=\s*(\d+[.,:]?\d*)[\)}\]]")

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

        metadata = []
        titles = []
        lines = [x.strip() for x in ocr_prose.split('\n') if x.strip()]

        for line in lines:

            # Fix some common number replacements in OCR
            line = line.replace('§', '5').replace('$', '5').replace('£', '[-')

            overall_match = OVERALL_LINE_RE.match(line)
            if not overall_match:
                titles.append(line)
            else:
                title, i_squared_str, probability_str = overall_match.groups()
                titles.append(title)
                metadata.append((forgiving_float(i_squared_str), forgiving_float(probability_str)))

                if title == "Overall":
                    break

        # having got the titles, now try to find the values
        values = ForestPlot._decode_table_values_ocr(ocr_prose)

        # now see if we can extract the weights from the last n lines
        weights = [forgiving_float(x) for x in lines[-1 * len(values):]]

        if len(metadata) == 1:
            if len(titles) != len(values):
                raise ValueError
            return [StataTableResults(titles, values, weights, metadata[0][0], metadata[0][1], 'Overall')]

        # else we assume multichart

        plots = []

        while titles:
            sub_title = titles[0]
            if len(titles) > 1:
                titles = titles[1:]
            index = None
            try:
                index = titles.index('Subtotal')
            except ValueError:
                try:
                    index = titles.index('Overall')
                except ValueError:
                    pass
            if index is None:
                break

            sub_titles = titles[:index + 1]
            sub_values = values[:index + 1]
            sub_weights = weights[:index + 1]

            titles = titles[index + 1:]
            values = values[index + 1:]
            weights = weights[index + 1:]

            plots.append(StataTableResults(sub_titles, sub_values, sub_weights, metadata[0][0], metadata[0][1], sub_title))
            metadata = metadata[1:]

        return plots

    @staticmethod
    def _decode_table_lines_ocr(ocr_prose):

        titles = []
        values = []
        weights = []

        title = None
        i_squared = None
        probability = None

        lines = [x.strip() for x in ocr_prose.split('\n') if x.strip()]
        for line in lines:

            # Fix some common number replacements in OCR
            line = line.replace('§', '5').replace('$', '5').replace('£', '[-')

            matches = TABLE_LINE_PARSE_RE.match(line)
            if not matches:
                continue
            groups = matches.groups()
            title = groups[0]
            try:
                value = (forgiving_float(groups[1]), forgiving_float(groups[2]), forgiving_float(groups[3]))
                value = sanity_check_values(value)

                overall_match = OVERALL_LINE_RE.match(title)
                if overall_match:
                    title = overall_match.groups()[0]
                    i_squared = forgiving_float(overall_match.groups()[1])
                    probability = forgiving_float(overall_match.groups()[2])

                titles.append(title)
                values.append(value)

                weight = forgiving_float(groups[-1])
                weights.append(weight)
            except AttributeError:
                continue

        if title is None:
            raise ValueError

        return StataTableResults(titles, values, weights, i_squared, probability, title)

    def _process_body(self):
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

                horizontal_results = StataTableResults([], [], [], None, None, '')
                vertical_results = StataTableResults([], [], [], None, None, '')
                try:
                    horizontal_results = self._decode_table_lines_ocr(ocr_prose)
                except ValueError:
                    pass
                try:
                    vertical_results = self._decode_table_columnwise_ocr(ocr_prose)[0]
                except (ValueError, IndexError):
                    pass

                results = horizontal_results
                if len(vertical_results.titles) > len(horizontal_results.titles):
                    results = vertical_results

                if results[0]:
                    data = zip(results.titles, results.values, results.weights)
                    flattened_data = [(title, value[0], value[1], value[2], weight) for title, value, weight in data]
                    self.primary_table.add_data(flattened_data)
                    if results.i_squared is not None:
                        self.overall_effect["i^2"] = results.i_squared
                    if results.probability is not None:
                        self.overall_effect["p"] = results.probability
                    self.primary_table.add_title("Data")

        else:
            # treat as multiple graphs, will add later

            for threshold in range(50, 80, 2):
                output_ocr_name = os.path.join(self.image_directory, "body.{0}.txt".format(threshold))
                ocr_prose = open(output_ocr_name, 'r').read()

                try:
                    result_list = self._decode_table_columnwise_ocr(ocr_prose)
                except ValueError:
                    continue
                for index in range(len(result_list)):
                    results = result_list[index]
                    if results[0]:
                        data = zip(results.titles, results.values, results.weights)
                        flattened_data = [(title, value[0], value[1], value[2], weight) for title, value, weight in data]
                        if not flattened_data:
                            continue
                        table = self.get_table(index)
                        table.add_data(flattened_data)
                        if results.title == "Overall":
                            self.overall_effect["i^2"] = results.i_squared
                            self.overall_effect["p"] = results.probability
                        table.add_title(results.title)



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
            count += 1



    def process(self):
        """Process the possible Stata forest plot."""
        self._process_header()
        if not self.summary:
            raise InvalidForestPlot

        self._process_body()
