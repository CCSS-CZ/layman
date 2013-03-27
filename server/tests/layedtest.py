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

    def test_delete(self):
        # TODO: make sure the layer exists

        # uncomment to delete
        # this deletes the feature type and layer
        # however, this does not (and should not) delete the data store.
        # if the layer is published as above, this is an issue, as it cannot be then published again.
        #self.le.deleteLayer("TestWS", "line_crs")
        pass

        # TODO: test

if __name__ == "__main__":
   suite = unittest.TestLoader().loadTestsFromTestCase(LayEdTestCase)
   unittest.TextTestRunner(verbosity=2).run(suite)
