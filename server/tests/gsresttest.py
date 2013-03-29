import os,sys
import unittest
import ConfigParser

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
INSTALL_DIR = os.path.abspath(os.path.join(TEST_DIR,".."))
sys.path.append(os.path.join(INSTALL_DIR))

# TODO: add tests for testing http GET, POST... methods beside the function calls

from layman.layed.gsrest import GsRest

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

    def test_getLayer(self):
        # TODO: find out the ws & name automatically
        layer = self.gs.getLayer("TestWS","line_crs")
        print layer
        # TODO: Add test

    def test_getFeatureType(self):
        # TODO: find out the ws,ds & name automatically
        ft = self.gs.getFeatureType("TestWS","line_crs","line_crs")
        print ft
        # TODO: Add test

    def test_getUrl(self):
        url = "http://erra.ccss.cz/geoserver/rest/workspaces/TestWS/datastores/line_crs/featuretypes/line_crs.json"
        result = self.gs.getUrl(url)
        print result

if __name__ == "__main__":
   suite = unittest.TestLoader().loadTestsFromTestCase(GsRestTestCase)
   unittest.TextTestRunner(verbosity=2).run(suite)
