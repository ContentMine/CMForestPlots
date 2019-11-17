"""Module for managing the forest plot data extraction."""

import json
import os
import subprocess

import openpyxl

from forestplots.papers import Paper
from forestplots.plots import InvalidForestPlot
from forestplots.spssplots import SPSSForestPlot
from forestplots.stataplots import StataForestPlot
from forestplots.projections import Projections
from forestplots.skeleton import Skeleton
from forestplots.results import Results

USE_DOCKER = True
try:
    USE_DOCKER = os.environ["FORESTPLOT_USE_DOCKER"] == "yes"
except KeyError:
    pass

IMAGE_NAME = "forestplot"



class Controller():
    """Runs the overall forest plot collecting code."""

    def __init__(self, project_directory):
        self.project_directory = project_directory

    def docker_wrapper(self, command, args):
        """Call a normami command in a docker container."""
        subprocess.run(["docker", "run", "-it", "--rm", "-v", f"{self.project_directory}:/tmp/project",
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

    def save_results(self, papers):
        """Save a workbook containing a summary of all plots."""
        res = Results(papers)
        res.save(os.path.join(self.project_directory, "results.xlsx"))


    def main(self):
        """This is the main method of the tool."""
        if not os.path.isfile(os.path.join(self.project_directory, "make_project.json")):
            print(f"Generating CProject in {self.project_directory}...")
            self.normami("ami-makeproject", ["--rawfiletypes", "html,pdf,xml", "--omit", "template.xml"])

        raw_project_contents = [os.path.join(self.project_directory, x) for x in os.listdir(self.project_directory)]
        project_contents = [x for x in raw_project_contents if os.path.isdir(x)]


        self.normami("ami-pdf")

        self.normami("ami-filter", ["--small", "small", "--duplicate", "duplicate", "--monochrome", "monochrome"])


        papers = []
        for ctree in project_contents:
            paper = Paper(ctree)
            papers.append(paper)

            pdf_images_dir = os.path.join(ctree, "pdfimages")
            try:
                imagedirs = [os.path.join(pdf_images_dir, x) for x in os.listdir(pdf_images_dir) if x.startswith("image.")]
            except FileNotFoundError:
                # Most likely we've hit other dirs in the corpus, like .git
                continue
            for imagedir in imagedirs:
                skeleton = Skeleton(imagedir)
                plot = None
                if skeleton.likely_spss():
                    os.rename(os.path.join(imagedir, "lines.png"),
                              os.path.join(imagedir, "spss.png"))
                    plot = SPSSForestPlot(imagedir, skeleton)
                elif skeleton.likely_stata():
                    os.rename(os.path.join(imagedir, "lines.png"),
                              os.path.join(imagedir, "stata.png"))
                    plot = StataForestPlot(imagedir, skeleton)

                if not plot:
                    continue

                try:
                    plot.break_up_image()
                    plot.process()
                except InvalidForestPlot:
                    pass
                else:
                    paper.plots.append(plot)
                    plot.save()

        self.save_results(papers)

