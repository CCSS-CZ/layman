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
    workdir = None
    cfg = None

    def setUp(self):
        cfg = ConfigParser.SafeConfigParser()
        cfg.read((os.path.join(TEST_DIR,"tests.cfg")))
        self.le = LayEd(cfg)
        self.gsr = GsRest(cfg)
        self.config = cfg
        self.workdir = os.path.abspath(os.path.join(TEST_DIR,"workdir","data"))

    # TODO: add tests for POST /layed?myLayer

    def test_01_publish(self):
        
        # Checks #

        # Check if the layer is not already there
        #(head, cont) = self.gsr.getLayer("dragouni", "line_crs")
        #self.assertNotEquals("200", head["status"], "The layer line_crs already exists. Please, remove it manually." )

        # Check if the style is not already there
        #(head, cont) = self.gsr.getStyle("dragouni", "line_crs")
        #self.assertNotEquals("200", head["status"], "The style line_crs already exists. Please, remove it manually." )

        # Check if the data store is not already there
        #(head, cont) = self.gsr.getDataStore("dragouni", "line_crs")
        #print "*** Check if the data store is not already there ***"
        #print 'getDataStore("dragouni", "line_crs")'
        #print head
        #print cont
        #self.assertNotEquals(True, "dataStore" in cont, "The data store line_crs already exists. Please, remove it manually." )
        #self.assertNotEquals("200", head["status"], "The data store line_crs already exists. Please, remove it manually." )

        # Publish #

        # Publish line_crs in workspace dragouni
        self.le.publish(fsDir=self.workdir, dbSchema=None, gsWorkspace="dragouni", fileName="line_crs.shp")

        # Test #

        # Check if the layer is there
        (head, cont) = self.gsr.getLayer("dragouni", "line_crs")
        self.assertEquals("200", head["status"], "The layer line_crs is not there. Was it created under another name?")

        # Check the style of the layer
        layerJson = json.loads(cont)
        styleName = layerJson["layer"]["defaultStyle"]["name"]
        self.assertEquals("line_crs", styleName, "The layer is there, but it has wrong style assinged.")

        # Check if the style is there
        (head, cont) = self.gsr.getStyle("dragouni", "line_crs")
        self.assertEquals("200", head["status"], "The style line_crs is not there." )

    #def test_02_delete(self):

        # Checks #

        # Check that the layer is there
        #(head, cont) = self.gsr.getLayer("dragouni", "line_crs")
        #self.assertEquals("200", head["status"], "The layer line_crs is not there. Was it created under another name?")

        # Check that the style is there
        #(head, cont) = self.gsr.getStyle("dragouni", "line_crs")
        #self.assertEquals("200", head["status"], "The style line_crs is not there." )

        # Delete #

        # Delete layer (including feature type, style and datastore)
        #self.le.deleteLayer(workspace="dragouni", layer="line_crs", deleteStore=True)

        # Test #

        # Check that the layer is not there
        #(head, cont) = self.gsr.getLayer("dragouni", "line_crs")
        #self.assertNotEquals("200", head["status"], "The layer line_crs still exists, should be already deleted." )

        # Check that the style is not there
        #(head, cont) = self.gsr.getStyle("dragouni", "line_crs")
        #self.assertNotEquals("200", head["status"], "The style line_crs already exists, should be already deleted." )

        # Check that the data store is not there
        #(head, cont) = self.gsr.getDataStore("dragouni", "line_crs")
        #self.assertNotEquals("200", head["status"], "The data store line_crs already exists, should be already deleted." )

if __name__ == "__main__":
   suite = unittest.TestLoader().loadTestsFromTestCase(LayEdTestCase)
   unittest.TextTestRunner(verbosity=2).run(suite)
