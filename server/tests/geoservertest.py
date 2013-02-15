import os,sys
import unittest
import ConfigParser

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
INSTALL_DIR = os.path.abspath(os.path.join(TEST_DIR,".."))
sys.path.append(os.path.join(INSTALL_DIR))

# TODO: add tests for testing http GET, POST... methods beside the gs.get_style... functions

from layman.geoserver import GeoServer
from geoserver.catalog import Catalog

style="""<?xml version="1.0" encoding="UTF-8"?><sld:StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:sld="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:gml="http://www.opengis.net/gml" version="1.0.0"><sld:NamedLayer><sld:Name>tmp_polygon</sld:Name><sld:UserStyle><sld:Name>tmp_polygon</sld:Name><sld:Title>Default Polygon</sld:Title><sld:Abstract>A sample style that draws a polygon</sld:Abstract><sld:FeatureTypeStyle><sld:Name>name</sld:Name><sld:Rule><sld:Name>rule1</sld:Name><sld:Title>Gray Polygon with Black Outline</sld:Title><sld:Abstract>A polygon with a gray fill and a 1 pixel black outline</sld:Abstract><sld:PolygonSymbolizer><sld:Fill><sld:CssParameter name="fill">#CC3333</sld:CssParameter></sld:Fill><sld:Stroke/></sld:PolygonSymbolizer></sld:Rule></sld:FeatureTypeStyle></sld:UserStyle></sld:NamedLayer></sld:StyledLayerDescriptor>"""

class GeoServerTestCase(unittest.TestCase):
    """Test of the file manager"""

    gs = None
    workdir = None

    def setUp(self):
        cfg = ConfigParser.SafeConfigParser()
        cfg.read((os.path.join(TEST_DIR,"tests.cfg")))
        self.gs = GeoServer(cfg)

        self.workdir = os.path.abspath(os.path.join(TEST_DIR,"workdir","data"))

        gsUrl = self.gs.config.get("GeoServer", "url")
        gsUser = self.gs.config.get("GeoServer", "user")
        gsPassword = self.gs.config.get("GeoServer", "password")
        self.direct_gs = Catalog(gsUrl, gsUser, gsPassword)

    def tearDown(self):

        class Req:
            href=self.gs.config.get("GeoServer", "url") + "/styles/tmp_polygon"

        if self.direct_gs.get_style("tmp_polygon"):
            self.direct_gs.delete(Req())

    ### LAYERS ###

    def test_getLayers(self):
        layers = self.gs.getLayers()
        print layers
        # TODO: Add test

    def test_getLayer(self):
        layers = self.gs.getLayers()
        layer = self.gs.getLayer(layers[0].name)
        print layer
        # TODO: Add test

    ### FEATURE STORE ###

    def test_createFeatrueStore(self):
        # TODO: make sure that source files exist

        # check / delete layer
        line_layer = self.direct_gs.get_layer("line_crs0")
        if line_layer is not None:
            self.direct_gs.delete(line_layer)

        # check / delete feature type
        #
        # sorry - it is not possible to delete feature type with gsconfig.py
        #
        # example in test 
        # https://github.com/dwins/gsconfig.py/blob/master/test/catalogtests.py#L424
        # only shows how to disable it        
        #
        # FOR NOW, PLEASE REMOVE THE FEATURE TYPE "line_crs0" MANUALLY
        #
        #line_feature = self.direct_gs.get_featuretype("line_crs0") # this function does not exist
        #if line_feature is not None:
        #    self.direct_gs.delete(line_feature)

        # TODO: remove the feature type using the gs rest api itself 

        # check / delete data store
        # line_store = self.direct_gs.get_store("line_crs")
        # if line_store is not None:
        #    self.direct_gs.delete(line_store)

        self.assert_(self.direct_gs.get_layer("line_crs1") is None)

        self.gs.createFeatureStore(self.workdir,"TestWS","line_crs")

        # Another problem - gs.createFeatureStore DOES NOT return the resource URI
        # - hence WE DON'T know the name of the created layer!

        # TODO: use the gs rest api itself and find out the name of the created layer 
        # - whether it is line_crs0, line_crs1 or what...

        self.assert_(self.direct_gs.get_layer("line_crs1") is not None)

    ### STYLES ###

    def test_getStyle(self):
        """Test get style"""

        style = self.gs.getStyle("line")
        self.assertTrue(style.find("<sld:Name>line</sld:Name>")>0)

    def test_postStyle(self):
        """Test get files function"""

        global style
        self.gs.postStyle("tmp_polygon",style)
        # TODO: add test
        # FIXME: UploadError: SLD file styles/tmp_polygon.sld.sld already exists.

    def test_putStyle(self):
        """Test get files function"""

        global style
        self.gs.postStyle("tmp_polygon",style)
        self.gs.putStyle("tmp_polygon",style)
        # TODO: add test
        # FIXME: UploadError: SLD file styles/tmp_polygon.sld.sld already exists.

if __name__ == "__main__":
   suite = unittest.TestLoader().loadTestsFromTestCase(GeoServerTestCase)
   unittest.TextTestRunner(verbosity=2).run(suite)
