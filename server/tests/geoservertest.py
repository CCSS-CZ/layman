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

    def setUp(self):
        cfg = ConfigParser.SafeConfigParser()
        cfg.read((os.path.join(TEST_DIR,"tests.cfg")))
        self.gs = GeoServer(cfg)
    
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

    def test_putStyle(self):
        """Test get files function"""

        global style
        self.gs.postStyle("tmp_polygon",style)
        self.gs.putStyle("tmp_polygon",style)
        # TODO: add test

if __name__ == "__main__":
   suite = unittest.TestLoader().loadTestsFromTestCase(GeoServerTestCase)
   unittest.TextTestRunner(verbosity=2).run(suite)
