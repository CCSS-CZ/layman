import os,sys
import unittest
import ConfigParser

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
INSTALL_DIR = os.path.abspath(os.path.join(TEST_DIR,".."))
sys.path.append(os.path.join(INSTALL_DIR))

import json
from layman.layed import LayEd
from layman.layed import DbMan

class LayEdTestCase(unittest.TestCase):
    """Test of the auth module"""

    le = None # LayEd
    dbm = None # DbMan
    config = None

    def setUp(self):
        cfg = ConfigParser.SafeConfigParser()
        cfg.read((os.path.join(TEST_DIR,"tests.cfg")))
        cfg.set("FileMan","testdir",TEST_DIR)
        self.le = LayEd(cfg)
        self.dbm = DbMan(cfg)
        self.config = cfg

    def test_getData(self):
        
        roles = [ 
                    { 
                      "roleName": "hasici",
                      "roleTitle": "FireMen"
                    },
                    {
                     "roleName": "aagroup",
                     "roleTitle": "AA Group"
                    }
                ]  

        print "*** roles ***"
        print roles

        print "***  getData() ... ***"
        head, cont = self.le.getData(roles, userName='hsrs')
        print "headers"
        print head
        print "response"
        print cont

        #head, cont = self.le.getDataDirect(roles)
        #print "***  getDataDirect() ***"
        #print "headers"
        #print head
        #print "response"
        #print cont

        print "*** syncing ... ***"
        head, cont = self.le.syncDataPad(roles)
        print "headers"
        print head
        print "response"
        print cont

        print "***  getData() ... ***"
        head, cont = self.le.getData(roles, userName='hsrs')
        print "headers"
        print head
        print "response"
        print cont

if __name__ == "__main__":
   suite = unittest.TestLoader().loadTestsFromTestCase(LayEdTestCase)
   unittest.TextTestRunner(verbosity=2).run(suite)
