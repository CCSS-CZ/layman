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
    """Test of the Layer Editor"""

    le = None # LayEd
    workdir = None
    config = None

    def setUp(self):
        cfg = ConfigParser.SafeConfigParser()
        cfg.read((os.path.join(TEST_DIR,"tests.cfg")))
        self.le = LayEd(cfg)
        self.config = cfg

        self.workdir = os.path.abspath(os.path.join(TEST_DIR,"workdir","data"))

    # TODO: add tests for POST /layed?myLayer

    def test_getLayers(self):
        r1 = {}
        r1["roleName"] = "hasici"
        r1["roleTitle"] = "Hasici Markvarec"
        r2 = {}
        r2["roleName"] = "pprd"
        r2["roleTitle"] = "PRD"
        roles = [r1,r2]

        headers, response = self.le.getLayers(roles)
        #print "*** TEST *** getLayers() ***"
        #print headers
        #print response

        responseJson = json.loads(response)

        self.assertEquals(True, responseJson[0]["featureType"]["enabled"], "FeatureType check failed")
        self.assertEquals("VECTOR", responseJson[0]["layer"]["type"], "Layer check failed")
        self.assertEquals(True, responseJson[0]["ws"] in ["hasici","pprd"], "Workspace check failed")
        self.assertEquals(True, responseJson[0]["roleTitle"] in ["Hasici Markvarec","PRD"], "roleTitle check failed")

    def test_cloneStyle(self):
        
        self.le.cloneStyle(fromWorkspace=None, fromStyle="polygon", toWorkspace="pprd", toStyle="MyNewPolygon")

        gsr = GsRest(self.config)
        (head, cont) = gsr.getStyleSld(workspace="pprd", styleName="MyNewPolygon")
        print " *** TEST *** clone style 1 ***"
        print head
        print cont

        self.le.cloneStyle(fromWorkspace="pprd", fromStyle="MyNewPolygon", toWorkspace=None, toStyle="YourNewPolygon")

        (head, cont) = gsr.getStyleSld(workspace=None, styleName="YourNewPolygon")
        print " *** TEST *** clone style 2 ***"
        print head
        print cont

    def test_getLayerConfig(self):

        retval = self.le.getLayerConfig("TestWS","line_crs")
        retval = json.loads(retval)
        self.assertEquals( "VECTOR", retval["layer"]["type"], "Layer is wrong" )
        self.assertEquals( "TestWS", retval["featureType"]["namespace"]["name"], "Feature Type is wrong" )

    def test_putLayerConfig(self):
        ''' Get Layer and Feature Type
        Layer -> Change 'Enabled' to 'False' 
        Feature Type -> Change 'Abstract'
        Test and change it back.
        '''
        # Prepare
        layer = self.le.getLayerConfig("TestWS","line_crs") # GET Layer & Feature Type
        #print "*** TEST *** received: ***"
        #print layer
        layer = json.loads(layer)                           # string -> json
        self.assertNotEquals( False, layer["layer"]["enabled"], "Please enable the layer" ) # layer: enabled
        self.assertNotEquals( "Abstract has changed", layer["featureType"]["abstract"], "Please change the abstract" ) # feature type: abstract

        # Change
        layer["layer"]["enabled"] = False               # layer: enabled
        layer["featureType"]["abstract"] = "Abstract has changed" # feature type: abstract
        layer = json.dumps(layer)                         # json -> string 
        #print "*** TEST *** sending: ***"
        #print layer
        self.le.putLayerConfig("TestWS","line_crs",layer) # PUT Layer & Feature Type

        # Test
        layer = self.le.getLayerConfig("TestWS","line_crs") # GET Layer & Feature Type
        layer = json.loads(layer)                           # string -> json
        #print 'layer["layer"]["enabled"]'
        #print layer["layer"]["enabled"]
        self.assertEquals( False, layer["layer"]["enabled"], "Layer change failed" ) # layer: enabled
        self.assertEquals( "Abstract has changed", layer["featureType"]["abstract"], "Feature Type change failed" ) # feature type: abstract

        # Change it back
        layer["layer"]["enabled"] = True
        layer["featureType"]["abstract"] = "Hello Dolly!"
        layer = json.dumps(layer)
        self.le.putLayerConfig("TestWS","line_crs",layer)

if __name__ == "__main__":
   suite = unittest.TestLoader().loadTestsFromTestCase(LayEdTestCase)
   unittest.TextTestRunner(verbosity=2).run(suite)
