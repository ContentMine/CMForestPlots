"""Module containing plot management."""

import os
import re

import openpyxl

from forestplots.helpers import forgiving_float

TABLE_VALUE_SPLIT_RE = re.compile(r'([-~]{0,1}\d+[.,:]\d*\s*[/\[\({][-~]{0,1}\d+[.,:]\d*\s*,\s*[-~]{0,1}\d+[.,:]\d*[\]}\)])')
TABLE_VALUE_GROK_RE = re.compile(r'([-~]{0,1}\d+[.,:]\d*)\s*[/\[\({]([-~]{0,1}\d+[.,:]\d*)\s*,\s*([-~]{0,1}\d+[.,:]\d*)[\]}\)]')

class InvalidForestPlot(Exception):
    """Raised if during processing we realise this isn't a valid forest plot."""

class ForestPlot():
    """Represents a single forest plot image held within a ctree."""

    def __init__(self, image_directory):
        self.image_directory = image_directory

        self.summary = {}
        self.hetrogeneity = {}
        self.overall_effect = {}

        self.table_data = []

    def add_summary_information(self, estimator_type=None, model_type=None, confidence_interval=None):
        """Add summary information about the forest plot."""
        if estimator_type:
            self.summary["Esimator type"] = estimator_type
        if model_type:
            self.summary["Model type"] = model_type
        if confidence_interval:
            self.summary["Confidence interval"] = confidence_interval

    def add_table_data(self, data):
        """Adds more data about the table."""
        if not data:
            raise ValueError
        if not self.table_data:
            self.table_data = [data]
        else:
            if len(self.table_data[0]) == len(data):
                self.table_data.append(data)
            elif len(self.table_data[0]) < len(data):
                self.table_data = [data]

    @staticmethod
    def _decode_table_values_ocr(ocr_prose):

        # Fix some common number replacements in OCR
        ocr_prose = ocr_prose.replace('§', '5').replace('£', '[-')

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

    def _collapse_table(self):
        if not self.table_data:
            return []
        if len(self.table_data) == 1:
            return self.table_data[0]

        mode_data = []
        for i in range(len(self.table_data[0])):
            final_row = []
            for datum in range(4):
                data = []
                for table in self.table_data:
                    data.append(table[i][datum])
                mode = max(set(data), key=data.count)
                final_row.append(mode)
            mode_data.append(tuple(final_row))
        return mode_data

    def is_valid(self):
        """Based on the data collected, do we think this is a valid plot?"""
        return self.table_data != []

    def save(self):
        """Writes the plot to an excel worksheet."""
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.title = "Summary"
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
        if self.table_data:
            mode_table = self._collapse_table()
            for value in mode_table:
                worksheet.cell(row=count, column=2, value=value[0])
                worksheet.cell(row=count, column=3, value=value[1])
                worksheet.cell(row=count, column=4, value=value[2])
                worksheet.cell(row=count, column=5, value=value[3])
                count += 1

        workbook.save(os.path.join(self.image_directory, "results.xlsx"))
