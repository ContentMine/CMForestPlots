"""Wrapper for projections.xml made by normami"""

import collections
import os
import xml.etree.ElementTree as ET

HorizontalLine = collections.namedtuple('HorizontalLine', 'y x1 x2')
VerticalLine = collections.namedtuple('VerticalLine', 'x y1 y2')

HEAL_SIZE = 200

class Projections:
    """Wrapper for normami projections.xml file."""

    def __init__(self, path):
        self._tree = ET.parse(path)
        self.horizontal_lines = []
        self.vertical_lines = []

        line_groups = self._tree.findall('{http://www.w3.org/2000/svg}g')
        if len(line_groups) != 2:
            raise AttributeError

        raw_horizontal_lines = []
        raw_vertical_lines = []
        for group in line_groups:
            if group.attrib['class'] == 'horizontallines':
                for line in list(group):
                    raw_horizontal_lines.append(HorizontalLine(float(line.attrib['y1']),
                                                               float(line.attrib['x1']),
                                                              float(line.attrib['x2'])))
            elif group.attrib['class'] == 'verticallines':
                for line in list(group):
                    raw_vertical_lines.append(VerticalLine(float(line.attrib['x1']),
                                                           float(line.attrib['y1']),
                                                            float(line.attrib['y2'])))

        # see if we have lines that need joining due to tiny gaps
        groups = {}
        for line in raw_horizontal_lines:
            try:
                groups[line.y].append(line)
            except KeyError:
                groups[line.y] = [line]

        for current_group in groups.values():
            current_group.sort(key=lambda l: l.x1)

            last_line = None
            for i in range(len(current_group) + 1):

                if i == len(current_group):
                    if last_line:
                        self.horizontal_lines.append(last_line)
                    break

                this_line = current_group[i]
                if not last_line:
                    last_line = this_line
                    continue

                if this_line.x1 - last_line.x2 < HEAL_SIZE:
                    last_line = HorizontalLine(last_line.y, last_line.x1, this_line.x2)
                else:
                    self.horizontal_lines.append(last_line)
                    last_line = this_line

        groups = {}
        for line in raw_vertical_lines:
            try:
                groups[line.x].append(line)
            except KeyError:
                groups[line.x] = [line]

        for current_group in groups.values():
            current_group.sort(key=lambda l: l.y1)

            last_line = None
            for i in range(len(current_group) + 1):

                if i == len(current_group):
                    if last_line:
                        self.vertical_lines.append(last_line)
                    break

                this_line = current_group[i]
                if not last_line:
                    last_line = this_line
                    continue

                if this_line.y1 - last_line.y2 < HEAL_SIZE:
                    last_line = VerticalLine(last_line.x, last_line.y1, this_line.y2)
                else:
                    self.vertical_lines.append(last_line)
                    last_line = this_line

    def save(self):
        """Save the cleaned tree."""

        line_groups = self._tree.findall('{http://www.w3.org/2000/svg}g')

        for group in line_groups:
            for child in list(group):
                group.remove(child)
            if group.attrib['class'] == 'horizontallines':
                for line in self.horizontal_lines:
                    node = ET.Element("line")
                    node.attrib["x1"] = f"{line.x1}"
                    node.attrib["x2"] = f"{line.x2}"
                    node.attrib["y1"] = f"{line.y}"
                    node.attrib["y2"] = f"{line.y}"
                    group.append(node)
            if group.attrib['class'] == 'verticallines':
                for line in self.vertical_lines:
                    node = ET.Element("line")
                    node.attrib["x1"] = f"{line.x}"
                    node.attrib["x2"] = f"{line.x}"
                    node.attrib["y1"] = f"{line.y1}"
                    node.attrib["y2"] = f"{line.y2}"
                    group.append(node)

        self._tree.write(open(os.path.join(os.path.split(path)[0], "clean.xml"), "wb"))


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
