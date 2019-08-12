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
from forestplots.results import Results

USE_DOCKER = True
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

        needs_pdf_parsing = False
        for ctree in project_contents:
            if not os.path.isdir(os.path.join(ctree, "pdfimages")):
                needs_pdf_parsing = True
                break
        if needs_pdf_parsing:
            self.normami("ami-pdf")

            self.normami("ami-filter", ["--small", "small", "--duplicate", "duplicate", "--monochrome", "monochrome"])

            for threshold in ["90"]:
                print(f"Testing with threshold {threshold}")
                self.normami("ami-image", ["--inputname", "raw", "--sharpen", "sharpen4", "--threshold", threshold,
                                           "--despeckle", "true"])

                self.normami("ami-pixel", ["--projections", "--yprojection", "0.4",
                                           "--xprojection", "0.7", "--lines", "--minheight", "1", "--rings", "-1",
                                           "--islands", "0",
                                           "--inputname", "raw_s4_thr_{0}_ds".format(threshold)])
#                                            "--templateinput", "raw_s4_thr_{0}/projections.xml".format(threshold),
#                                            "--templateoutput", "template.xml",
#                                            "--templatexsl", "/org/contentmine/ami/tools/spssTemplate1.xsl"])

#                 self.normami("ami-pixel", ["--inputname", f"raw_s4_thr_{threshold}_ds",
#                                            "--templateinput", f"raw_s4_thr_{threshold}/projections.xml",
#                                            "--templateoutput", "template.xml",
#                                            "--templatexsl", "/org/contentmine/ami/tools/spssTemplate1.xsl"])
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
                                           "--inputname", f"raw_s4_thr_{threshold}_ds",])
#                                            "--templateinput", f"raw_s4_thr_{threshold}_ds/projections.xml",
#                                            "--templateoutput", "template.xml",
#                                            "--templatexsl", "/org/contentmine/ami/tools/stataTemplate1.xsl"])

#                 self.normami("ami-pixel", ["--inputname", f"raw_s4_thr_{threshold}_ds",
#                                            "--templateinput", f"raw_s4_thr_{threshold}/projections.xml",
#                                            "--templateoutput", "template.xml",
#                                            "--templatexsl", "/org/contentmine/ami/tools/stataTemplate1.xsl"])
                # ami-pixel seems to ignore the --outputDirectory argument, so let us fix that
                for ctree in project_contents:
                    pdf_images_dir = os.path.join(ctree, "pdfimages")
                    imagedirs = [os.path.join(pdf_images_dir, x) for x in os.listdir(pdf_images_dir) if x.startswith("image.")]
                    for imagedir in imagedirs:
                        os.rename(os.path.join(imagedir, f"raw_s4_thr_{threshold}_ds"),
                                  os.path.join(imagedir, f"stata_{threshold}"))


                # now get rid of projections that don't look like spss or stata
                for ctree in project_contents:
                    pdf_images_dir = os.path.join(ctree, "pdfimages")
                    imagedirs = [os.path.join(pdf_images_dir, x) for x in os.listdir(pdf_images_dir) if x.startswith("image.")]
                    for imagedir in imagedirs:
                        spss_projection = Projections(os.path.join(imagedir, f"spss_{threshold}", "projections.xml"))
                        if spss_projection.likely_spss():
                            os.rename(os.path.join(imagedir, f"spss_{threshold}"),
                                      os.path.join(imagedir, "target_spss"))
#                             self.normami("ami-pixel", ["--templateinput", "target_spss/clean.xml",
#                                                        "--templateoutput", "template.xml",
#                                                        "--templatexsl", "/org/contentmine/ami/tools/spssTemplate1.xsl"])

                        stata_projection = Projections(os.path.join(imagedir, f"stata_{threshold}", "projections.xml"))
                        if stata_projection.likely_stata():
                            os.rename(os.path.join(imagedir, f"stata_{threshold}"),
                                      os.path.join(imagedir, "target_stata"))
#                             self.normami("ami-pixel", ["--templateinput", "target_stata/clean.xml",
#                                                        "--templateoutput", "template.xml",
#                                                        "--templatexsl", "/org/contentmine/ami/tools/stataTemplate1.xsl"])

#                 self.normami("ami-forestplot",
#                              ["--segment", "--template", "target_spss/template.xml"])
#                 self.normami("ami-forestplot",
#                              ["--segment", "--template", "target_stata/template.xml"])

        papers = []
        for ctree in project_contents:
            paper = Paper(ctree)
            papers.append(paper)

            pdf_images_dir = os.path.join(ctree, "pdfimages")
            imagedirs = [os.path.join(pdf_images_dir, x) for x in os.listdir(pdf_images_dir) if x.startswith("image.")]
            for imagedir in imagedirs:

                plot = None
                if os.path.isdir(os.path.join(imagedir, "target_spss")):
                    plot = SPSSForestPlot(imagedir)
                elif os.path.isdir(os.path.join(imagedir, "target_stata")):
                    plot = StataForestPlot(imagedir)
                else:
                    continue

                try:
                    plot.break_up_image()
                    plot.process()
                except InvalidForestPlot:
                    pass
                else:
                    paper.plots.append(plot)
                    plot.save()


        summary = {}
        for paper in papers:
            summary = [os.path.join(x.image_directory, "results.xlsx") for x in paper.plots]


            print(f"Paper {paper.ctree_directory} has {len(paper.plots)} plots.")
            for plot in paper.plots:
                print(f"\t{plot.image_directory}")

        with open(os.path.join(self.project_directory, "forestplots.json"), "w") as results_file:
            results_file.write(json.dumps(summary))

        self.save_results(papers)
