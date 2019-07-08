"""Common helper code."""


def forgiving_float(float_string):
    """Takes a string and tries to clear up common OCR errors before trying to convert to a float."""
    return float(float_string.replace('~', '-').replace(',', '.'))
