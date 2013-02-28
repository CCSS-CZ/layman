import os,sys
import unittest
import ConfigParser

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
INSTALL_DIR = os.path.abspath(os.path.join(TEST_DIR,".."))
sys.path.append(os.path.join(INSTALL_DIR))

import json
from layman.layed import LayEd

class LayEdTestCase(unittest.TestCase):
    """Test of the auth module"""

    le = None # LayEd
    workdir = None
    cfg = None

    def setUp(self):
        cfg = ConfigParser.SafeConfigParser()
        cfg.read((os.path.join(TEST_DIR,"tests.cfg")))
        self.le = LayEd(cfg)
        self.cfg = cfg

        self.workdir = os.path.abspath(os.path.join(TEST_DIR,"workdir","data"))

    # TODO: add tests for POST /layed?myLayer

    def test_publish(self):
        from geoserver.catalog import Catalog
        gsUrl = self.cfg.get("GeoServer", "url")
        gsUser = self.cfg.get("GeoServer", "user")
        gsPassword = self.cfg.get("GeoServer", "password")
        self.direct_gs = Catalog(gsUrl, gsUser, gsPassword)

        # Intro
        self.assertEquals( True, None == self.direct_gs.get_layer("line_crs"), "The layer line_crs already exists. Please, remove it manually." )
        #self.assertEquals( True, None == self.direct_gs.get_store("line_crs"), "The store line_crs already exists. Please, remove it manually." )

        # Action
        self.le.publish(fsDir=self.workdir, dbSchema=None, gsWorkspace="TestWS", fileName="line_crs.shp")

        # Test
        self.assertEquals( False, None == self.direct_gs.get_layer("line_crs"), "The layer line_crs is not there. Was it created under another name?" )

    def test_getLayerConfig(self):

        retval = self.le.getLayerConfig("TestWS","line_crs")
        retval = json.loads(retval)
        self.assertEquals( "VECTOR", retval["layer"]["type"], "Layer is wrong" )
        self.assertEquals( "TestWS", retval["featureType"]["namespace"]["name"], "Feature Type is wrong" )

    def test_putLayerConfig(self):
        # Prepare
        layer = self.le.getLayerConfig("TestWS","line_crs")
        layer = json.loads(layer)
        self.assertNotEquals( "false", layer["layer"]["enabled"], "Please enable the layer" )
        self.assertNotEquals( "Abstract has changed", layer["featureType"]["abstract"], "Please change the abstract" )

        # Change
        layer["layer"]["enabled"] = 'false'
        layer["featureType"]["astract"] = "Abstract has changed"
        layer = json.dumps(layer)
        self.le.putLayerConfig("TestWS","line_crs",layer)

        # Test
        layer = self.le.getLayerConfig("TestWS","line_crs")
        layer = json.loads(layer)
        self.assertEquals( "false", layer["layer"]["enabled"], "Layer change failed" )
        self.assertEquals( "Abstract has changed", layer["featureType"]["abstract"], "Feature Type change failed" )

        # Change it back
        layer["layer"]["enabled"] = 'true'
        layer["featureType"]["astract"] = "Hello Dolly!"
        layer.dumps(layer)
        #self.le.putLayerConfig("TestWS","line_crs",layer)

if __name__ == "__main__":
   suite = unittest.TestLoader().loadTestsFromTestCase(LayEdTestCase)
   unittest.TextTestRunner(verbosity=2).run(suite)
