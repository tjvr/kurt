
import pickle
import glob
import os
import unittest
from kurt import kurt

SELF_PATH = os.path.dirname(os.path.abspath(__file__))


class CorpusTests(unittest.TestCase):
    def _test_file(self, path):
        # For now, just check we can load the file.
        p = kurt.Project.load(path)

        # TODO: try saving it, and run scratch-diff against the original!
        # TODO: write `scratch-diff`...
        # TODO use @nathan's sb2 Validator on the saved files.



# Define tests declaratively

def create_test(path):
    _, filename = os.path.split(path)
    name, ext = os.path.splitext(filename)
    test_name = "".join(c for c in name if c.isalpha())

    def test_file(self):
        self._test_file(path)
    setattr(CorpusTests, "test_file_{}".format(test_name), test_file)

files = glob.glob(os.path.join(SELF_PATH, 'scratch-corpus/sb2/*.sb2'))
for path in files:
    create_test(path)

