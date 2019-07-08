"""Module containing plot management."""

import os

import openpyxl

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
            if len(self.table_data) == len(data):
                self.table_data.append(data)
            elif len(self.table_data) < len(data):
                self.table_data = [data]

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
            for title, value in self.table_data[0].items():
                worksheet.cell(row=count, column=2, value=title)
                worksheet.cell(row=count, column=3, value=value[0])
                worksheet.cell(row=count, column=4, value=value[1])
                worksheet.cell(row=count, column=5, value=value[2])
                count += 1

        workbook.save(os.path.join(self.image_directory, "results.xlsx"))
