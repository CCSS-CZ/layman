import os,sys
import unittest
import ConfigParser
from web import application as app
import urllib
import json

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
INSTALL_DIR = os.path.abspath(os.path.join(TEST_DIR,".."))
sys.path.append(os.path.join(INSTALL_DIR))

import layman
from layman import *

class ClientTestCase(unittest.TestCase):
    """Testing the whole service (request/response) from the client point of
    view"""

    lm = None
    laymanapp = None
    
    def setUp(self):
        cfg = ConfigParser.SafeConfigParser()
        cfg.read((os.path.join(TEST_DIR,"tests.cfg")))
        cfg.set("FileMan","testdir",TEST_DIR)
    
        # start the server
        # FIXME not sure, if this is a good start
        self.laymanapp = app(("/layman/(.*)","LayMan"), globals())

    def tearDown(self):
        pass

    def test_getfiles(self):
        # FIXME not sure, if this works
        r = self.laymanapp.request("/layman/fileman/getfiles.json");
        j = json.dumps(r.data)

        self.assertEquals(6,len(j),"number of files")

if __name__ == "__main__":
   suite = unittest.TestLoader().loadTestsFromTestCase(ClientTestCase)
   unittest.TextTestRunner(verbosity=2).run(suite)
