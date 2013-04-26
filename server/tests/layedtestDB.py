import os,sys
import unittest
import ConfigParser

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
INSTALL_DIR = os.path.abspath(os.path.join(TEST_DIR,".."))
sys.path.append(os.path.join(INSTALL_DIR))

import json
from layman.layed import LayEd
from layman.layed import GsRest

class LayEdTestCase(unittest.TestCase):
    """Test of the auth module"""

    le = None # LayEd
    gsr = None # GsRest
    workdir = None
    config = None

    def setUp(self):
        cfg = ConfigParser.SafeConfigParser()
        cfg.read((os.path.join(TEST_DIR,"tests.cfg")))
        cfg.set("FileMan","testdir",TEST_DIR)
        self.le = LayEd(cfg)
        self.gsr = GsRest(cfg)
        self.config = cfg
        self.workdir = os.path.abspath(os.path.join(TEST_DIR,"workdir","data"))

    def test_01_publish(self):
        
        ws = "mis"
        ds = "erraPublic"
        ll = "line_crs"
        head, cont = self.le.createFtFromDb(ws, ds, ll)
        print "*** test publish ***"
        print "headers"
        print head
        print "response"
        print cont

if __name__ == "__main__":
   suite = unittest.TestLoader().loadTestsFromTestCase(LayEdTestCase)
   unittest.TextTestRunner(verbosity=2).run(suite)
