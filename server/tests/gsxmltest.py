import os,sys
import unittest
import ConfigParser

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
INSTALL_DIR = os.path.abspath(os.path.join(TEST_DIR,".."))
sys.path.append(os.path.join(INSTALL_DIR))

from layman.layed.gsxml import GsXml
import xml.etree.ElementTree as Xml

class GsXmlTestCase(unittest.TestCase):

    gsx = None
    gsdir = None

    def setUp(self):
        cfg = ConfigParser.SafeConfigParser()
        cfg.read((os.path.join(TEST_DIR,"tests.cfg")))
        self.gsx = GsXml(cfg)

        self.gsdir = self.gsx.config.get("GeoServer", "gsdir")

    def test_setLayerStyle(self):
        
        ### Check ###
        # Armenia roads layer has a no-workspace style 'simple_roads'
        
        # Layer
        layerPath = self.gsx.getLayerPath(layerWorkspace="Armenia", dataStoreName="arm", layerName="ARM_roads")
        layerTree = Xml.parse(layerPath)
        layerRoot = layerTree.getroot()
        layerOrigStyleId = layerRoot.find("./defaultStyle/id").text

        # Original style
        origStylePath = self.gsx.getStyleXmlPath(styleWorkspace=None, styleName="simple_roads")
        origStyleTree = Xml.parse(origStylePath)
        origStyleRoot = origStyleTree.getroot()
        origStyleId   = origStyleRoot.find("./id").text

        # Check
        self.assertEquals(layerOrigStyleId, origStyleId, "The <id> of the default style of the layer doesn't match the id of the expected style")

        ### Change ###
        # Set layer style to 'pprd:railroad'

        self.gsx.setLayerStyle(layerWorkspace="Armenia", dataStoreName="arm", layerName="ARM_roads", styleWorkspace="pprd", styleName="railroad")

        ### Test ###

        # Re-load the layer
        layerPath = self.gsx.getLayerPath(layerWorkspace="Armenia", dataStoreName="arm", layerName="ARM_roads")
        layerTree = Xml.parse(layerPath)
        layerRoot = layerTree.getroot()
        layerNewStyleId = layerRoot.find("./defaultStyle/id").text
        
        # New style
        newStylePath = self.gsx.getStyleXmlPath(styleWorkspace="pprd", styleName="railroad")
        newStyleTree = Xml.parse(newStylePath)
        newStyleRoot = newStyleTree.getroot()
        newStyleId   = newStyleRoot.find("./id").text
    
        # Check
        self.assertEquals(layerNewStyleId, newStyleId, "Layer has wrong style assigned")

        ### Change back ###
        self.gsx.setLayerStyle(layerWorkspace="Armenia", dataStoreName="arm", layerName="ARM_roads", styleWorkspace=None, styleName="simple_roads")

        ### Test again ###
        
        # Re-load the layer
        layerPath = self.gsx.getLayerPath(layerWorkspace="Armenia", dataStoreName="arm", layerName="ARM_roads")
        layerTree = Xml.parse(layerPath)
        layerRoot = layerTree.getroot()
        layerStyleBackId = layerRoot.find("./defaultStyle/id").text
        
        # Check
        self.assertEquals(layerStyleBackId, origStyleId, "The second style changed failed")

if __name__ == "__main__":
   suite = unittest.TestLoader().loadTestsFromTestCase(GsXmlTestCase)
   unittest.TextTestRunner(verbosity=2).run(suite)
