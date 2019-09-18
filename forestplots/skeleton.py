
import collections
import os
import random

import cv2
import numpy as np


HorizontalLine = collections.namedtuple('HorizontalLine', 'y x1 x2')
VerticalLine = collections.namedtuple('VerticalLine', 'x y1 y2')

def auto_canny(image, sigma=0.33):
	# compute the median of the single channel pixel intensities
	v = np.median(image)

	# apply automatic Canny edge detection using the computed median
	lower = int(max(0, (1.0 - sigma) * v))
	upper = int(min(255, (1.0 + sigma) * v))
	edged = cv2.Canny(image, lower, upper)

	# return the edged image
	return edged

class Skeleton:

    def __init__(self, image_directory):

        print(image_directory)

        img = cv2.imread(os.path.join(image_directory, "raw.png"))

        self.height, self.width = img.shape[0:2]

        self.horizontal_lines = []
        self.vertical_lines = []

        low_threshold = 100
        high_threshold = 150
        #edges = cv2.Canny(img, low_threshold, high_threshold)
        edges = auto_canny(img)

        cv2.imwrite("/tmp/edges.png", edges)

        rho = 1  # distance resolution in pixels of the Hough grid
        theta = np.pi / 180  # angular resolution in radians of the Hough grid
        threshold = 15  # minimum number of votes (intersections in Hough grid cell)
        min_line_length = 150  # minimum number of pixels making up a line
        max_line_gap = 30  # maximum gap in pixels between connectable line segments
        line_image = np.copy(img) * 0  # creating a blank to draw lines on

        # Run Hough on edge detected image
        # Output "lines" is an array containing endpoints of detected line segments
        lines = cv2.HoughLinesP(edges, rho, theta, threshold, np.array([]),
                            min_line_length, max_line_gap)

        try:
            vertical_lines = [x for x in lines if x[0][0] == x[0][2]]
        except TypeError:
            return

        # debounce vertical_lines lines
        vertical_lines.sort(key=lambda a: a[0][0])
        clean = vertical_lines[:1]
        for i in range(len(vertical_lines) - 1):
            line = vertical_lines[i + 1]
            last = clean[-1]
            if abs(last[0][0] - line[0][0]) < 20:
                # two very close line, just keep the longest
                last_len = last[0][1] - last[0][3]
                line_len = line[0][1] - line[0][3]
                if line_len > last_len:
                    clean = clean[:-1]
                    clean.append(line)
            else:
                clean.append(line)
        vertical_lines = clean

        # sort by size, biggest to smallest
        vertical_lines.sort(key=lambda a: a[0][1] - a[0][3], reverse=True)

        try:
            main_line = vertical_lines[0]
        except IndexError:
            return
        self.vertical_lines = [VerticalLine(a[0][0], a[0][3], a[0][1]) for a in vertical_lines[:2]]

        # filter: y1 == y2 and x1 < main_line.x1 and y2 > main_line.y1  - and y1 > main_line.y1 and y1 < main_line.y2
        horizontal_lines = [a for a in lines if a[0][1] == a[0][3] and (a[0][0] < main_line[0][0] < a[0][2]) and (main_line[0][3] <= a[0][3] <= main_line[0][1])]


        # debounce horizontal_lines
        horizontal_lines.sort(key=lambda a: a[0][1])
        clean = horizontal_lines[:1]
        for i in range(len(horizontal_lines) - 1):
            line = horizontal_lines[i + 1]
            last = clean[-1]
            if abs(last[0][1] - line[0][1]) < 20:
                # two very close line, just keep the longest
                last_len = last[0][2] - last[0][0]
                line_len = line[0][2] - line[0][0]
                if line_len > last_len:
                    clean = clean[:-1]
                    clean.append(line)
            else:
                clean.append(line)
        horizontal_lines = clean

        # now filter the horizontal lines, keeping the ones at the clostest to top and bottom
        try:
            top_line = horizontal_lines[0]
            bottom_line = horizontal_lines[-1]
            self.horizontal_lines = [HorizontalLine(x[0][1], x[0][0], x[0][2]) for x in [top_line, bottom_line]]
        except IndexError:
            self.horizontal_lines = []

#
#         horizontal_lines.sort(key=lambda a: a[0][2] - a[0][0], reverse=True)
#         horizontal_lines = horizontal_lines[:2]
#         horizontal_lines.sort(key=lambda a: a[0][1])


        # Find the longest vertical line_image - ideally just one
        for vline in self.vertical_lines:
            _ = cv2.line(line_image,(vline.x, vline.y1),(vline.x, vline.y2),
                (128 + int(random.random() * 128), 128, 128),1)

        for hline in self.horizontal_lines:
            _ = cv2.line(line_image,(hline.x1, hline.y), (hline.x2, hline.y),
                (128, 128 + int(random.random() * 128), 128),1)
        #
        #
        # lines_edges = cv2.addWeighted(img, 0.8, line_image, 1, 0)

        cv2.imwrite(os.path.join(image_directory, "lines.png"), line_image)


    def likely_spss(self):
        """Guess if this is likely an SPSS plot."""

        try:
            main_line = self.vertical_lines[0]
            top_line = self.horizontal_lines[0]
            bottom_line = self.horizontal_lines[1]
        except IndexError:
            return False

        # is the top line over 95% of the image width? if not, bin it
        if (float(top_line.x2 - top_line.x1) / float(self.width)) < 0.9:
            return False

        # is the bottom line ledd than 60% of the image width? if not, bin it
        if (float(bottom_line.x2 - bottom_line.x1) / float(self.width)) > 0.6:
            return False

        # does the top line sit close to the start of the vertical line?
        length = float(main_line.y2 - main_line.y1)
        offset = float(top_line.y - main_line.y1)

        if (offset / length) > 0.25:
            return False

        # does the bottom line sit close to the end of the vertical line?
        length = float(main_line.y2 - main_line.y1)
        offset = float(bottom_line.y - main_line.y1)

        if (offset / length) < 0.9:
            return False

        return True


    def likely_stata(self):
        """Guess if this is likely a stata plot."""

        try:
            main_line = self.vertical_lines[0]
            bottom_line = self.horizontal_lines[-1]
        except IndexError:
            return False

        # is the bottom line over 95% of the image width? if not, bin it
        if (float(bottom_line.x2 - bottom_line.x1) / float(self.width)) < 0.9:
            return False

        # check the position of the lower line is near the bottom of the horizontal line
        horizontal_line_y = bottom_line.y
        length = float(main_line.y2 - main_line.y1)
        offset = float(horizontal_line_y - main_line.y1)

        if (offset / length) < 0.85:
            return False

        # is the vertical line roughly central?
        vertical_line_x = main_line.x
        length = float(bottom_line.x2 - bottom_line.x1)
        offset = float(vertical_line_x - bottom_line.x1)

        if not 0.25 < (offset / length) < 0.75:
            return False

        return True
