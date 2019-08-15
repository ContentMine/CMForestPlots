#!/usr/bin/env python

import random
import sys

import cv2
import numpy as np

def auto_canny(image, sigma=0.33):
	# compute the median of the single channel pixel intensities
	v = np.median(image)

	# apply automatic Canny edge detection using the computed median
	lower = int(max(0, (1.0 - sigma) * v))
	upper = int(min(255, (1.0 + sigma) * v))
	edged = cv2.Canny(image, lower, upper)

	# return the edged image
	return edged

fn = sys.argv[1]
img = cv2.imread(fn)

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


if 0:
    for line in lines:
        for x1,y1,x2,y2 in line:
#             if True:
            if x1 == x2 or y1 == y2:
                _ = cv2.line(line_image,(x1,y1),(x2,y2),
                    (128 + int(random.random() * 128), 128 + int(random.random() * 128), 128 + int(random.random() * 128)),1)
else:
    vertical_lines = [x for x in lines if x[0][0] == x[0][2]]

    main_line = vertical_lines[0]


    # filter: y1 == y2 and x1 < main_line.x1 and x2 > main_line.x1  - and y1 > main_line.y1 and y1 < main_line.y2
    horizontal_lines = [a for a in lines if a[0][1] == a[0][3] and (a[0][0] < main_line[0][0] < a[0][2]) and (main_line[0][3] <= a[0][3] <= main_line[0][1])]

    # first sort lines by y order
    horizontal_lines.sort(key=lambda a: a[0][1])

    # debounce horizontal lines
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

    # debounce vertical_lines
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

    # now sort lines by length
    horizontal_lines.sort(key=lambda a: a[0][2] - a[0][0], reverse=True)
    vertical_lines.sort(key=lambda a: a[0][1] - a[0][3], reverse=True)




    # Find the longest vertical line_image - ideally just one
    for line in vertical_lines:
        for x1,y1,x2,y2 in line:
            _ = cv2.line(line_image,(x1,y1),(x2,y2),
                (128 + int(random.random() * 128), 128, 128),1)

    for line in horizontal_lines:
        for x1,y1,x2,y2 in line:
            _ = cv2.line(line_image,(x1,y1),(x2,y2),
                (128, 128 + int(random.random() * 128), 128),1)

#
# lines_edges = cv2.addWeighted(img, 0.8, line_image, 1, 0)

cv2.imwrite("/tmp/lines.png", line_image)
