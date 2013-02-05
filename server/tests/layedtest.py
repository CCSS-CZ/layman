import os,sys
import unittest
import ConfigParser

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
INSTALL_DIR = os.path.abspath(os.path.join(TEST_DIR,".."))
sys.path.append(os.path.join(INSTALL_DIR))

from layman.layed import LayEd

class LayEdTestCase(unittest.TestCase):
    """Test of the auth module"""

    le = None # LayEd
    workdir = None

    def setUp(self):
        cfg = ConfigParser.SafeConfigParser()
        cfg.read((os.path.join(TEST_DIR,"tests.cfg")))
        self.le = LayEd(cfg)

        self.workdir = os.path.abspath(os.path.join(TEST_DIR,"workdir","data"))

    # TODO: add tests for POST /layed?myLayer

    def test__importShapeFile(self):
        """Test importShapeFile() function:
        Make sure that test file exists.
        If testing table exists, drop it.
        Call importShapeFile() function.
        Select from the test table to test the result. """

        import psycopg2
        testFilePath = self.workdir+"/" + self.le.config.get("LayEdTest","testfile")
        testTable = self.le.config.get("LayEdTest","testtable")

        # Make sure that file exists        
        self.assertEquals(os.path.exists(testFilePath), True, "The testing file " + testFilePath + " cannot be found")

        # If exists remove the test table  

        # Connection string
        dbname = self.le.config.get("LayEd","dbname")
        dbuser = self.le.config.get("LayEd","dbuser")
        dbhost = self.le.config.get("LayEd","dbhost")
        dbpass = self.le.config.get("LayEd","dbpass")
        connectionString = "dbname='"+dbname+"' user='"+dbuser+"' host='"+dbhost+"' password='"+dbpass+"'"

        try:
            print "Trying to connect to \"" + connectionString + "\"..."
            conn = psycopg2.connect(connectionString)
            print "OK"

            # Drop table if exists
            dropTable = "DROP TABLE IF EXISTS " + testTable + ";";
            cur = conn.cursor()
            print "Trying to drop table if exists " + testTable + "..."
            cur.execute(dropTable) 
            conn.commit()
            print "OK"

        except Exception as e:
            print "Database error (trying to drop the test table): " 
            print e
            raise e

        # Import
        self.le.importShapeFile(testFilePath)

        # Select from the test table - test the result
        selectFrom = "SELECT * FROM " + testTable + ";"
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
   suite = unittest.TestLoader().loadTestsFromTestCase(LayEdTestCase)
   unittest.TextTestRunner(verbosity=2).run(suite)
