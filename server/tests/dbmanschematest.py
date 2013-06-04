import os,sys
import unittest
import ConfigParser

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
INSTALL_DIR = os.path.abspath(os.path.join(TEST_DIR,".."))
sys.path.append(os.path.join(INSTALL_DIR))

import psycopg2
from layman.layed.dbman import DbMan

class DbManTestCase(unittest.TestCase):
    """Test of the dbman module"""

    dbm = None # DbMan
    workdir = None
    cfg = None

    def setUp(self):
        cfg = ConfigParser.SafeConfigParser()
        cfg.read((os.path.join(TEST_DIR,"tests.cfg")))
        self.dbm = DbMan(cfg)
        self.cfg = cfg

        self.workdir = os.path.abspath(os.path.join(TEST_DIR,"workdir","data"))

    def test__createSchema(self):

        testSchema = "OranzovyExpress"

        self.dbm.createSchemaIfNotExists(testSchema)

if __name__ == "__main__":
   suite = unittest.TestLoader().loadTestsFromTestCase(DbManTestCase)
   unittest.TextTestRunner(verbosity=2).run(suite)
