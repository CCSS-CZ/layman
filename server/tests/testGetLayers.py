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

    def test_wsDsCreate(self):
        self.le.createWorkspaceIfNotExists("DeltaDunaje")
        self.le.createWorkspaceIfNotExists("DeltaDunaje")

        self.le.createDataStoreIfNotExists("hasici", "DeltaDunaje")

    def test_getLayers(self):
        r1 = {}
        r1["roleName"] = "hasici"
        r1["roleTitle"] = "Hasici Markvarec"
        r2 = {}
        r2["roleName"] = "policajti"
        r2["roleTitle"] = "Svestky"
        roles = [r1,r2]

        headers, response = self.le.getLayers(roles)
        #print "*** TEST *** getLayers() ***"
        #print headers
        #print response

        responseJson = json.loads(response)

        self.assertEquals(True, responseJson[0]["featureType"]["enabled"], "FeatureType check failed")
        self.assertEquals("VECTOR", responseJson[0]["layer"]["type"], "Layer check failed")
        self.assertEquals(True, responseJson[0]["ws"] in ["hasici","pprd"], "Workspace check failed")
        self.assertEquals(True, responseJson[0]["roleTitle"] in ["Hasici Markvarec","Svestky"], "roleTitle check failed")

if __name__ == "__main__":
   suite = unittest.TestLoader().loadTestsFromTestCase(LayEdTestCase)
   unittest.TextTestRunner(verbosity=2).run(suite)
