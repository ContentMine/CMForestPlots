"""Module containing plot management."""

import os
import re

import openpyxl

from forestplots.helpers import forgiving_float, sanity_check_values

TABLE_VALUE_SPLIT_RE = re.compile(r'([-~]{0,1}\d+[.,: ]\d*\s*[/\[\({][-~]{0,1}\d+[.,: ]\d*\s*[.,]\s*[-~]{0,1}\d+[.,: ]\d*[\]}\)]|\(Excluded\))')
TABLE_VALUE_GROK_RE = re.compile(r'([-~]{0,1}\d+[.,: ]\d*)\s*[/\[\({]([-~]{0,1}\d+[.,: ]\d*)\s*[.,]\s*([-~]{0,1}\d+[.,: ]\d*)[\]}\)]')

NAME_RE = re.compile(r'^image\.([\d\.]+)_.*$')

class InvalidForestPlot(Exception):
    """Raised if during processing we realise this isn't a valid forest plot."""

class Table():
    """Representing the data of a single table."""

    def __init__(self):
        self.table_data = []
        self.title_list = []

    def add_data(self, data):
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

    def collapse_data(self):
        """Takes the mode of all the table data entered and returns it as a single table."""

        if not self.table_data:
            return []
        if len(self.table_data) == 1:
            return self.table_data[0]

        mode_data = []
        for i in range(len(self.table_data[0])):
            final_row = []
            for datum in range(len(self.table_data[0][i])):
                data = []
                for table in self.table_data:
                    data.append(table[i][datum])
                mode = max(set(data), key=data.count)
                final_row.append(mode)
            mode_data.append(tuple(final_row))
        return mode_data

    def add_title(self, title):
        if title:
            self.title_list.append(title)

    def collapse_titles(self):
        try:
            return max(set(self.title_list), key=self.title_list.count)
        except ValueError:
            return ""

class ForestPlot():
    """Represents a single forest plot image held within a ctree."""

    def __init__(self, image_directory):
        self.image_directory = image_directory

        self.summary = {}
        self.hetrogeneity = {}
        self.overall_effect = {}

        self.table_list = [Table()]

    @property
    def id(self):
        """Get a unique ID for the image."""
        basename = os.path.basename(self.image_directory)
        return NAME_RE.match(basename).groups()[0]

    def break_up_image(self):
        """Splits the forest plot image into sub-images required for OCR."""
        raise NotImplementedError

    def add_summary_information(self, estimator_type=None, model_type=None, confidence_interval=None):
        """Add summary information about the forest plot."""
        if estimator_type:
            self.summary["Esimator type"] = estimator_type
        if model_type:
            self.summary["Model type"] = model_type
        if confidence_interval:
            self.summary["Confidence interval"] = confidence_interval

    @property
    def primary_table(self):
        """Get the main table. Others may exist."""
        return self.table_list[0]

    def get_table(self, index):
        """Get one of the tables in this plot."""
        try:
            return self.table_list[index]
        except IndexError:
            # yes, this can blow up, yes that's deliberate
            self.table_list.append(Table())
            return self.table_list[index]


    @staticmethod
    def _decode_table_values_ocr(ocr_prose):

        # Fix some common number replacements in OCR
        ocr_prose = ocr_prose.replace('§', '5').replace('$', '5').replace('£', '[-')

        parts = TABLE_VALUE_SPLIT_RE.split(ocr_prose)
        values = []
        for part in parts:
            try:
                groups = TABLE_VALUE_GROK_RE.match(part).groups()
                value = (forgiving_float(groups[0]), forgiving_float(groups[1]), forgiving_float(groups[2]))
                value = sanity_check_values(value)

                values.append(value)
            except AttributeError:
                if part == "(Excluded)":
                    values.append(("Excluded", "Excluded", "Excluded"))
        return values

    def is_valid(self):
        """Based on the data collected, do we think this is a valid plot?"""
        return self.primary_table.table_data != []

    def _write_data_to_worksheet(self, worksheet):
        raise NotImplementedError

    def save(self):
        """Writes the plot to an excel worksheet."""
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.title = "Summary"

        self._write_data_to_worksheet(worksheet)

        workbook.save(os.path.join(self.image_directory, "results.xlsx"))

    def json_repr(self):
        """Creates a JSON compatible dictionary representation."""
        raise NotImplementedError
