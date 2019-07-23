"""Common helper code."""


def forgiving_float(float_string):
    """Takes a string and tries to clear up common OCR errors before trying to convert to a float."""
    return float(float_string.replace('~', '-').replace(',', '.').replace(':', '.').replace(';', '.').replace(' ', '.'))


def sanity_check_values(value):
    """We note that the leading - is often missed, but the ones within the block less so, so we
    have a sanity check here and see if adding a -ve to the first value helps"""

    if not value[1] < value[0] < value[2]:
        if value[1] < -value[0] < value[2]:
            value = (-value[0], value[1], value[2])
    return value
