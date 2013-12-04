import os,sys
import unittest
import ConfigParser
import json

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
INSTALL_DIR = os.path.abspath(os.path.join(TEST_DIR,".."))
sys.path.append(os.path.join(INSTALL_DIR))

from layman.layed.gsxml import GsXml
from layman.layed.gssec import GsSec
from layman.layed import LayEd
import xml.etree.ElementTree as Xml

class AccessControlTestCase(unittest.TestCase):

    gss = None
    gsx = None
    gsdir = None
    config = None

    def setUp(self):
        cfg = ConfigParser.SafeConfigParser()
        cfg.read((os.path.join(TEST_DIR,"tests.cfg")))
        self.gsx = GsXml(cfg)
        
        self.config = cfg
        self.gsdir = self.gsx.config.get("GeoServer", "gsdir")

    def test_AccessControl(self):
       
        # Test SECURE LAYER from LayEd

        le = LayEd(self.config)
 
        roleFer = le.secureLayer("hasici", "Ferrovie")
        rolePest = le.secureLayer("hasici", "Hasici Pest")
        roleAzov = le.secureLayer("policajti", "Policajti Azov")

        # TODO add tests

        # Make sure that:
        #   - Role READ_HASICI_FERROVIE exists // roles
        #   - and is assigned to "hasici" group // roles
        #   - hasici.Ferrovie.r = READ_HASICI_FERROVIE // layer.properties - require the role to read the layer

        # etc for other layers.

        # Test ACCESS GRANTING from LayEd

        le = LayEd(self.config)
        
        le.grantAccess(role, userlist, grouplist)
        le.grantAccess(roleFer, [], ["hasici","policajti"])
        le.grantAccess(rolePest, ["pepa"], ["hasici"])
        le.grantAccess(roleAzov, [], ["policajti"])

        # TODO add tests

        # Make sure that:
        #   - the corresponding roles are assigned to the appropriate users and groups


if __name__ == "__main__":
   suite = unittest.TestLoader().loadTestsFromTestCase(UserManTestCase)
   unittest.TextTestRunner(verbosity=2).run(suite)
