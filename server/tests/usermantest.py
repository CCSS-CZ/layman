import os,sys
import unittest
import ConfigParser
import json

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
INSTALL_DIR = os.path.abspath(os.path.join(TEST_DIR,".."))
sys.path.append(os.path.join(INSTALL_DIR))

from layman.layed.gsxml import GsXml
import xml.etree.ElementTree as Xml

class UserManTestCase(unittest.TestCase):

    gsx = None
    gsdir = None
    config = None

    def setUp(self):
        cfg = ConfigParser.SafeConfigParser()
        cfg.read((os.path.join(TEST_DIR,"tests.cfg")))
        self.gsx = GsXml(cfg)
        
        self.config = cfg
        self.gsdir = self.gsx.config.get("GeoServer", "gsdir")

    def test_createUserWithGroups(self):
        
        from layman.userprefs import UserPrefs
        up = UserPrefs(self.config)

        uj = {} # user json
        uj["screenName"] = "Jarek"
        uj["roles"] = []
        r1 = {}
        r1["roleName"]  = "drvostep2"
        r1["roleTitle"] = "Dr.Vostep"
        uj["roles"].append(r1)
        r2 = {}
        r2["roleName"]  = "pijan2"
        r2["roleTitle"] = "Dr.Inker"
        uj["roles"].append(r2)
        userJsonStr = json.dumps(uj)
        
        up.createUser(userJsonStr)


if __name__ == "__main__":
   suite = unittest.TestLoader().loadTestsFromTestCase(UserManTestCase)
   unittest.TextTestRunner(verbosity=2).run(suite)
