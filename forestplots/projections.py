"""Wrapper for projections.xml made by normami"""

import collections
import xml.etree.ElementTree as ET

HorizontalLine = collections.namedtuple('HorizontalLine', 'y x1 x2')
VerticalLine = collections.namedtuple('VerticalLine', 'x y1 y2')

class Projections:
    """Wrapper for normami projections.xml file."""

    def __init__(self, path):
        self._tree = ET.parse(path)
        self.horizontal_lines = []
        self.vertical_lines = []

        line_groups = self._tree.findall('{http://www.w3.org/2000/svg}g')
        if len(line_groups) != 2:
            raise AttributeError

        for group in line_groups:
            if group.attrib['class'] == 'horizontallines':
                for line in list(group):
                    self.horizontal_lines.append(HorizontalLine(float(line.attrib['y1']),
                                                                float(line.attrib['x1']),
                                                                float(line.attrib['x2'])))
            elif group.attrib['class'] == 'verticallines':
                for line in list(group):
                    self.vertical_lines.append(VerticalLine(float(line.attrib['x1']),
                                                            float(line.attrib['y1']),
                                                            float(line.attrib['y2'])))


    def likely_spss(self):
        """Guess if this is likely an SPSS plot."""
        return len(self.horizontal_lines) == 2 and len(self.vertical_lines) == 1

    def likely_stata(self):
        """Guess if this is likely a stata plot."""

        # The SPSS plots when run through the stata line processing will end up looking like stata plots in terms
        # of line counts, but they're upside down. So we use line count plus checking the horizontal line is near the
        # bottom of the plot, not the top.

        if not (len(self.horizontal_lines) == 1 and len(self.vertical_lines) == 1):
            return False

        horizontal_line_y = self.horizontal_lines[0].y
        vertical_line = self.vertical_lines[0]

        length = float(vertical_line.y2 - vertical_line.y1)
        offset = float(horizontal_line_y - vertical_line.y1)

        return (offset / length) > 0.9
