"""Module containing paper abstraction."""

import os

class Paper():
    """Represents a single paper ctree being processed by normami."""

    def __init__(self, ctree_directory):
        self.ctree_directory = ctree_directory
        self.plots = []

    @property
    def pmcid(self):
        """Return the PMCID for the paper."""
        return os.path.basename(self.ctree_directory).replace('pmc', '')

    @property
    def name(self):
        return os.path.basename(self.ctree_directory)


    def json_repr(self):
        """Return a JSON compatible dictionary."""

        return {"plots": [x.json_repr() for x in self.plots]}
