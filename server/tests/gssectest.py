import os,sys
import unittest
import ConfigParser

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
INSTALL_DIR = os.path.abspath(os.path.join(TEST_DIR,".."))
sys.path.append(os.path.join(INSTALL_DIR))

from layman.layed.gssec import GsSec

class GsSecTestCase(unittest.TestCase):

    gss = None
    gsdir = None

    def setUp(self):
        cfg = ConfigParser.SafeConfigParser()
        cfg.read((os.path.join(TEST_DIR,"tests.cfg")))
        self.gss = GsSec(cfg)

        self.gsdir = self.gss.config.get("GeoServer", "gsdir")

    def test_gsSec(self):

        self.gss.setRule("zednici", "mury", "w", ["MAJSTR", "PRIDAVAC"])
        self.gss.setRule("zednici", "*", "w", ["MAJSTR"])
        self.gss.secureWorkspace("drotari", ["ROLE_DROTAR","ROLE_POWER"])
        self.gss.writeLayerProp()

if __name__ == "__main__":
   suite = unittest.TestLoader().loadTestsFromTestCase(GsSecTestCase)
   unittest.TextTestRunner(verbosity=2).run(suite)
