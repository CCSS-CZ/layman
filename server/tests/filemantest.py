import os,sys
import unittest
import ConfigParser

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
INSTALL_DIR = os.path.abspath(os.path.join(TEST_DIR,".."))
sys.path.append(os.path.join(INSTALL_DIR))

from layman.fileman import FileMan

class FileManTestCase(unittest.TestCase):
    """Test of the file manager"""

    fm = None

    def setUp(self):
        cfg = ConfigParser.SafeConfigParser()
        cfg.read((os.path.join(TEST_DIR,"tests.cfg")))
        cfg.set("FileMan","testdir",TEST_DIR)
        self.fm = FileMan(cfg)

    def test_getDir(self):
        """Test dir"""

        workdir = os.path.abspath(os.path.join(TEST_DIR,"workdir","data"))

        self.assertTrue(os.path.samefile(workdir, self.fm.config.get("FileMan","targetdir")),
            "Make sure, that configuration works and that the data dir was found")

    def test_getFiles(self):
        """Test get files request"""

        # example of expected json response:
        # [
        #   {
        #       name: "file.shp",
        #       size: 1000000,
        #       prj: "epsg:4326",
        #       date: "2012-04-05 05:43",
        #       mimetype: "application/x-zipped-shp" 
        #   },
        #   ...
        # ]
        
        # NOTE: mimetypes should be handled according to https://portal.opengeospatial.org/files/?artifact_id=47860

        workdir = os.path.abspath(os.path.join(TEST_DIR,"workdir","data"))

        files = self.fm.getfiles()
        self.assertEquals(type(files), type([]), "List is an array")
        self.assertEquals(len(files), len(os.listdir(workdir)), "Number of files match")
        self.assertEquals(files[0].keys(),["name","size","prj","mimetype"],"File attributes are existing")


if __name__ == "__main__":
   suite = unittest.TestLoader().loadTestsFromTestCase(FileManTestCase)
   unittest.TextTestRunner(verbosity=2).run(suite)
