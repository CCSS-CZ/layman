import os,sys
import unittest
import ConfigParser

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
INSTALL_DIR = os.path.abspath(os.path.join(TEST_DIR,".."))
sys.path.append(os.path.join(INSTALL_DIR))

import json
from layman.layed import LayEd
from layman.layed.ckanapi import CkanApi

class LayEdCkanTestCase(unittest.TestCase):

    le = None # LayEd
    workdir = None
    cfg = None

    def setUp(self):
        cfg = ConfigParser.SafeConfigParser()
        cfg.read((os.path.join(TEST_DIR,"tests.cfg")))
        cfg.set("FileMan","testdir",TEST_DIR)
        self.le = LayEd(cfg)
        self.ckan = CkanApi(cfg)
        self.config = cfg
        self.workdir = os.path.abspath(os.path.join(TEST_DIR,"workdir","data"))


    def test_01_ckan(self):

        # Get CKAN packages (==datasets)
        strCkanPackages = self.le.getCkanPackages(roles=[], userName="", limit="10", offset="0")
        print strCkanPackages

if __name__ == "__main__":
   suite = unittest.TestLoader().loadTestsFromTestCase(LayEdCkanTestCase)
   unittest.TextTestRunner(verbosity=2).run(suite)
