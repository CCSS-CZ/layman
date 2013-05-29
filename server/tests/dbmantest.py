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

    def test__importShapeFile(self):
        """Test importShapeFile() function:
        Make sure that test file exists.
        If testing table exists, drop it.
        Call importShapeFile() function.
        Select from the test table to test the result. """

        testFilePath = self.workdir+"/" + self.dbm.config.get("DbManTest","testfile")
        #testTable = self.dbm.config.get("DbManTest","testtable")
        testTable = "pest"
        testSchema = self.dbm.config.get("DbManTest","testschema")

        # Make sure that file exists        
        self.assertEquals(os.path.exists(testFilePath), True, "The testing file " + testFilePath + " cannot be found")

        # If exists remove the test table  

        # Connection string
        dbname = self.dbm.config.get("DbMan","dbname")
        dbuser = self.dbm.config.get("DbMan","dbuser")
        dbhost = self.dbm.config.get("DbMan","dbhost")
        dbpass = self.dbm.config.get("DbMan","dbpass")
        connectionString = "dbname='"+dbname+"' user='"+dbuser+"' host='"+dbhost+"' password='"+dbpass+"'"

        try:
            print "Trying to connect to \"" + connectionString + "\"..."
            conn = psycopg2.connect(connectionString)
            print "OK"

            # Drop table if exists
            dropTable = "DROP TABLE IF EXISTS " + testSchema+"."+testTable + ";";
            cur = conn.cursor()
            print "Trying to drop table if exists " + testSchema+"."+ testTable + "..."
            cur.execute(dropTable) 
            conn.commit()
            print "OK"

        except Exception as e:
            print "Database error (trying to drop the test table): " 
            print e
            raise e

        # Import
        self.dbm.importShapeFile(testFilePath,testSchema)

        # Select from the test table - test the result
        selectFrom = "SELECT * FROM " + testSchema+"."+ testTable + ";"
        try:
            cur.execute(selectFrom)
            result = cur.fetchone()
            self.assertGreater(len(result), 0, "Unable to select from the test table")
            conn.commit

            # Close
            cur.close()
            conn.close()
        except Exception as e:
            print "Database error (trying to select from the test table): " 
            print e
            raise e

if __name__ == "__main__":
   suite = unittest.TestLoader().loadTestsFromTestCase(DbManTestCase)
   unittest.TextTestRunner(verbosity=2).run(suite)
