import os,sys
import unittest
import ConfigParser

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
INSTALL_DIR = os.path.abspath(os.path.join(TEST_DIR,".."))
sys.path.append(os.path.join(INSTALL_DIR))

# TODO: add tests for testing http GET, POST... methods beside the function calls

from layman.layed.geoserv import GsRest

class GsRestTestCase(unittest.TestCase):

    gs = None
    workdir = None

    def setUp(self):
        cfg = ConfigParser.SafeConfigParser()
        cfg.read((os.path.join(TEST_DIR,"tests.cfg")))
        self.gs = GsRest(cfg)

        self.workdir = os.path.abspath(os.path.join(TEST_DIR,"workdir","data"))

        gsUrl = self.gs.config.get("GeoServer", "url")
        gsUser = self.gs.config.get("GeoServer", "user")
        gsPassword = self.gs.config.get("GeoServer", "password")


    ### LAYERS ###

    def test_getLayers(self):
        layers = self.gs.getLayers()
        print layers
        # TODO: Add test

if __name__ == "__main__":
   suite = unittest.TestLoader().loadTestsFromTestCase(GsRestTestCase)
   unittest.TextTestRunner(verbosity=2).run(suite)
