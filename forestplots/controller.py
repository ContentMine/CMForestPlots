"""Module for managing the forest plot data extraction."""

import json
import os
import subprocess
#import xml.dom.minidom

from forestplots.plots import InvalidForestPlot
from forestplots.spssplots import SPSSForestPlot
from forestplots.projections import Projections

USE_DOCKER = False
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
                        IMAGE_NAME, command, "-p", "/tmp/project"] + args, capture_output=False)

    def normami(self, command, args=None):
        """Call a normami command."""
        if not args:
            args = []
        print("Calling {0}".format(command))
        if USE_DOCKER:
            self.docker_wrapper(command, args)
        else:
            subprocess.run([command, "-p", self.project_directory] + args, capture_output=False)
        print("Done")


    def main(self):
        """This is the main method of the tool."""
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

            self.normami("ami-filter", ["--small", "small", "--duplicate", "duplicate", "--monochrome", "monochrome"])

            for threshold in ["150"]:
                print("Testing with threshold {0}".format(threshold))
                self.normami("ami-image", ["--inputname", "raw", "--sharpen", "sharpen4", "--threshold", threshold,
                                           "--despeckle", "true"])

                self.normami("ami-pixel", ["--projections", "--yprojection", "0.4",
                                           "--xprojection", "0.7", "--lines", "--minheight", "1", "--rings", "-1",
                                           "--islands", "0",
                                           "--inputname", "raw_s4_thr_{0}_ds".format(threshold),
                                           "--templateinput", "raw_s4_thr_{0}/projections.xml".format(threshold),
                                           "--templateoutput", "template.xml",
                                           "--templatexsl", "/org/contentmine/ami/tools/spssTemplate1.xsl"])
                # ami-pixel seems to ignore the --outputDirectory argument, so let us fix that
                for ctree in project_contents:
                    pdf_images_dir = os.path.join(ctree, "pdfimages")
                    imagedirs = [os.path.join(pdf_images_dir, x) for x in os.listdir(pdf_images_dir) if x.startswith("image.")]
                    for imagedir in imagedirs:
                        os.rename(os.path.join(imagedir, "raw_s4_thr_{0}_ds".format(threshold)),
                                  os.path.join(imagedir, "spss_{0}".format(threshold)))

                self.normami("ami-pixel", ["--projections", "--yprojection", "0.8",
                                           "--xprojection", "0.6", "--lines", "--minheight", "1", "--rings", "-1",
                                           "--islands", "0",
                                           "--subimage", "statascale", "y", "LAST", "delta", "10", "projection", "x",
                                           "--inputname", "raw_s4_thr_{0}_ds".format(threshold),
                                           "--templateinput", "raw_s4_thr_{0}_ds/projections.xml".format(threshold),
                                           "--templateoutput", "template.xml",
                                           "--templatexsl", "/org/contentmine/ami/tools/stataTemplate1.xsl"])
                # ami-pixel seems to ignore the --outputDirectory argument, so let us fix that
                for ctree in project_contents:
                    pdf_images_dir = os.path.join(ctree, "pdfimages")
                    imagedirs = [os.path.join(pdf_images_dir, x) for x in os.listdir(pdf_images_dir) if x.startswith("image.")]
                    for imagedir in imagedirs:
                        os.rename(os.path.join(imagedir, "raw_s4_thr_{0}_ds".format(threshold)),
                                  os.path.join(imagedir, "stata_{0}".format(threshold)))


                # now get rid of projections that don't look like spss or stata
                for ctree in project_contents:
                    pdf_images_dir = os.path.join(ctree, "pdfimages")
                    imagedirs = [os.path.join(pdf_images_dir, x) for x in os.listdir(pdf_images_dir) if x.startswith("image.")]
                    for imagedir in imagedirs:
                        spss_projection = Projections(os.path.join(imagedir, "spss_{0}".format(threshold), "projections.xml"))
                        if spss_projection.likely_spss():
                            os.rename(os.path.join(imagedir, "spss_{0}".format(threshold)),
                                      os.path.join(imagedir, "target_spss_{0}".format(threshold)))

                        stata_projection = Projections(os.path.join(imagedir, "stata_{0}".format(threshold), "projections.xml"))
                        if stata_projection.likely_stata():
                            os.rename(os.path.join(imagedir, "stata_{0}".format(threshold)),
                                      os.path.join(imagedir, "target_stata_{0}".format(threshold)))

                self.normami("ami-forestplot",
                             ["--segment", "--template", "target_spss_{0}/template.xml".format(threshold)])
                self.normami("ami-forestplot",
                             ["--segment", "--template", "target_stata_{0}/template.xml".format(threshold)])


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
                paper.plots.append(plot)
                plot.save()

        summary = {}
        for paper in papers:
            summary = [os.path.join(x.image_directory, "results.xlsx") for x in paper.plots]


            print("Paper {1} has {0} plots.".format(len(paper.plots), paper.ctree_directory))
            for plot in paper.plots:
                print("\t{0}".format(plot.image_directory))

        with open(os.path.join(self.project_directory, "forestplots.json"), "w") as results_file:
            results_file.write(json.dumps(summary))
