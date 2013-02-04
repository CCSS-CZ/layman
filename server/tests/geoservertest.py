import os,sys
import unittest
import ConfigParser

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
INSTALL_DIR = os.path.abspath(os.path.join(TEST_DIR,".."))
sys.path.append(os.path.join(INSTALL_DIR))

# TODO: add tests for testing http GET, POST... methods beside the fm.getFiles()... functions
# TODO: uncomment & fix the test for getFileDetails once the function is ready

from layman.geoserver import Geoserver
from geoserver.catalog import Catalog

style="""<?xml version="1.0" encoding="UTF-8"?><sld:StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:sld="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:gml="http://www.opengis.net/gml" version="1.0.0"><sld:NamedLayer><sld:Name>tmp_polygon</sld:Name><sld:UserStyle><sld:Name>tmp_polygon</sld:Name><sld:Title>Default Polygon</sld:Title><sld:Abstract>A sample style that draws a polygon</sld:Abstract><sld:FeatureTypeStyle><sld:Name>name</sld:Name><sld:Rule><sld:Name>rule1</sld:Name><sld:Title>Gray Polygon with Black Outline</sld:Title><sld:Abstract>A polygon with a gray fill and a 1 pixel black outline</sld:Abstract><sld:PolygonSymbolizer><sld:Fill><sld:CssParameter name="fill">#CC3333</sld:CssParameter></sld:Fill><sld:Stroke/></sld:PolygonSymbolizer></sld:Rule></sld:FeatureTypeStyle></sld:UserStyle></sld:NamedLayer></sld:StyledLayerDescriptor>"""

class FileManTestCase(unittest.TestCase):
    """Test of the file manager"""

    fm = None
    workdir = None

    def setUp(self):
        cfg = ConfigParser.SafeConfigParser()
        cfg.read((os.path.join(TEST_DIR,"tests.cfg")))
        cfg.add_section("Geoserver")
        cfg.set("Geoserver","url","http://localhost:8080/geoserver/rest")
        cfg.set("Geoserver","user","admin")
        cfg.set("Geoserver","password","geoserver")
        self.gs = Geoserver(cfg)
        self.direct_gs = Catalog("http://localhost:8080/geoserver/rest",
                            "admin","geoserver")

    def tearDown(self):

        class Req:
            href="http://localhost:8080/geoserver/rest/styles/tmp_polygon"

        if self.direct_gs.get_style("tmp_polygon"):
            self.direct_gs.delete(Req())

    def test_getStyle(self):
        """Test get style"""

        style = self.gs.getStyle("line")
        self.assertTrue(style.find("<sld:Name>line</sld:Name>")>0)

    def test_postStyle(self):
        """Test get files function"""

        global style
        self.gs.postStyle("tmp_polygon",style)

    def test_putStyle(self):
        """Test get files function"""

        global style
        self.gs.postStyle("tmp_polygon",style)
        self.gs.putStyle("tmp_polygon",style)


if __name__ == "__main__":
   suite = unittest.TestLoader().loadTestsFromTestCase(FileManTestCase)
   unittest.TextTestRunner(verbosity=2).run(suite)
