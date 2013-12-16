import os,sys
import unittest
import ConfigParser
import json

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
INSTALL_DIR = os.path.abspath(os.path.join(TEST_DIR,".."))
sys.path.append(os.path.join(INSTALL_DIR))

from layman.auth import LaymanAuthLiferay
import xml.etree.ElementTree as Xml

class GetAllRolesTestCase(unittest.TestCase):

    gsdir = None
    config = None

    def setUp(self):
        cfg = ConfigParser.SafeConfigParser()
        cfg.read((os.path.join(TEST_DIR,"tests.cfg")))
        
        self.config = cfg

    def test_GetAllRoles(self):

        aut = LaymanAuthLiferay(self.config)
        roles = aut.getAllRolesStr()
        print roles       

if __name__ == "__main__":
   suite = unittest.TestLoader().loadTestsFromTestCase(GetAllRolesTestCase)
   unittest.TextTestRunner(verbosity=2).run(suite)
