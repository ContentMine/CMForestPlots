"""Module for managing the forest plot data extraction."""

import collections
import os
import re
import subprocess
#import xml.dom.minidom

from forestplots.helpers import forgiving_float
from forestplots.plots import InvalidForestPlot
from forestplots.spssplots import SPSSForestPlot

USE_DOCKER = True
IMAGE_NAME = "forestplot"

class Paper():
    """Represents a single paper ctree being processed by normami."""

    def __init__(self, ctree_directory):
        self.ctree_directory = ctree_directory
        self.plots = []

class Controller():
    """Runs the overall forest plot collecting code."""

    def __init__(self, project_directory):
        self.project_directory = project_directory

    def docker_wrapper(self, command, args):
        """Call a normami command in a docker container."""
        subprocess.run(["docker", "run", "-it", "--rm", "-v", "{0}:/tmp/project".format(self.project_directory),
                        IMAGE_NAME, command, "-p", "/tmp/project"] + args, capture_output=True)

    def normami(self, command, args=None):
        """Call a normami command."""
        if not args:
            args = []
        print("Calling {0}".format(command))
        if USE_DOCKER:
            self.docker_wrapper(command, args)
        else:
            subprocess.run([command, "-p", self.project_directory] + args, capture_output=True)
        print("Done")


    def main(self):

        if not os.path.isfile(os.path.join(self.project_directory, "make_project.json")):
            print("Generating CProject in {0}...".format(self.project_directory))
            self.normami("ami-makeproject", ["--rawfiletypes", "html,pdf,xml", "--omit", "template.xml"])

        raw_project_contents = [os.path.join(self.project_directory, x) for x in os.listdir(self.project_directory)]
        project_contents = [x for x in raw_project_contents if os.path.isdir(x)]

        needs_pdf_parsing = False
        for ctree in project_contents:
            if not os.path.isdir(os.path.join(ctree, "pdfimages")):
                needs_pdf_parsing = True
                break
        if needs_pdf_parsing:
            self.normami("ami-pdf")
            for threshold in ["150"]:
                print("Testing with threshold {0}".format(threshold))
                self.normami("ami-image", ["--sharpen", "sharpen4", "--threshold", threshold, "--despeckle", "true"])
                self.normami("ami-pixel", ["--projections", "--yprojection", "0.4",
                                           "--xprojection", "0.7", "--lines", "--minheight", "1", "--rings", "-1",
                                           "--islands", "0",
                                           "--inputname", "raw_s4_thr_{0}_ds".format(threshold),
                                           "--templateinput", "raw_s4_thr_{0}_ds/projections.xml".format(threshold),
                                           "--templateout", "template.xml",
                                           "--templatexsl", "/org/contentmine/ami/tools/spssTemplate.xsl"])

                self.normami("ami-forestplot",
                             ["--segment", "--template", "raw_s4_thr_{0}_ds/template.xml".format(threshold)])

        papers = []
        for ctree in project_contents:
            paper = Paper(ctree)
            papers.append(paper)

            pdf_images_dir = os.path.join(ctree, "pdfimages")
            imagedirs = [os.path.join(pdf_images_dir, x) for x in os.listdir(pdf_images_dir) if x.startswith("image.")]
            for imagedir in imagedirs:

                plot = SPSSForestPlot(imagedir)

                try:
                    plot.process()
                except InvalidForestPlot:
                    continue



                image_path = os.path.join(imagedir, "raw.body.table.png")
                if not os.path.isfile(image_path):
                    continue

                for threshold in range(50, 80, 2):
                    output_ocr_name = os.path.join(imagedir, "body.table.{0}.txt".format(threshold))
                    if not os.path.isfile(output_ocr_name):
                        output_image_name = os.path.join(imagedir, "body.table.{0}.png".format(threshold))
                        if not os.path.isfile(output_image_name):
                            subprocess.run(["convert", "-black-threshold", "{0}%".format(threshold),
                                            image_path, output_image_name])
                        subprocess.run(["tesseract", output_image_name, os.path.splitext(output_ocr_name)[0]],
                                       capture_output=True)

                    titles = []
                    raw_lines = open(output_ocr_name, 'r').readlines()
                    lines = [x for x in raw_lines if len(x.strip()) > 0]

                    for line in lines:
                        if line.startswith('Total'):
                            titles.append(line)
                            break
                        titles.append(line)

                    values = []
                    r = re.compile(r'^\s*([-~]{0,1}\d+[.,]{0,1}\d*)\s*[\[\({]([-~]{0,1}\d+[.,]{0,1}\d*)\s*,\s*([-~]{0,1}\d+[.,]{0,1}\d*)[\]}\)]\s*$')
                    for line in lines:
                        m = r.match(line)
                        if m:
                            g = m.groups()
                            try:
                                values.append((forgiving_float(g[0]), forgiving_float(g[1]), forgiving_float(g[2])))
                            except ValueError:
                                pass

                    if values and len(values) == len(titles):
                        data = collections.OrderedDict(zip(titles, values))
                        plot.add_table_data(data)

                image_path = os.path.join(imagedir, "raw.header.graphheads.png")
                if not os.path.isfile(image_path):
                    continue

                best_res = None
                for threshold in range(50, 80, 2):
                    output_ocr_name = os.path.join(imagedir, "header.graphheads.{0}.txt".format(threshold))
                    if not os.path.isfile(output_ocr_name):
                        output_image_name = os.path.join(imagedir, "header.graphheads.{0}.png".format(threshold))
                        if not os.path.isfile(output_image_name):
                            subprocess.run(["convert", "-black-threshold", "{0}%".format(threshold),
                                            image_path, output_image_name])
                        subprocess.run(["tesseract", output_image_name, os.path.splitext(output_ocr_name)[0]],
                                       capture_output=True)

                    ocr_prose = open(output_ocr_name).read()
                    r = re.compile(r"^.*\n\s*(M-H|IV)[\s.,]*(Fixed|Random)[\s.,]*(\d+)%\s*C[ilI!].*", re.MULTILINE)
                    m = r.match(ocr_prose)
                    if m:
                        best_res = m.groups()
                if best_res:
                    plot.add_summary_information(estimator_type=best_res[0], model_type=best_res[1],
                                                 confidence_interval=best_res[2])

                if plot.is_valid():
                    paper.plots.append(plot)
                plot.save()

        for paper in papers:
            print("Paper {1} has {0} plots.".format(len(paper.plots), paper.ctree_directory))
            for plot in paper.plots:
                print("\t{0}".format(plot.image_directory))
