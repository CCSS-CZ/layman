import os,sys
import unittest
import ConfigParser

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
INSTALL_DIR = os.path.abspath(os.path.join(TEST_DIR,".."))
sys.path.append(os.path.join(INSTALL_DIR))

# TODO: add tests for postFile, putFile, deleteFile
# TODO: add tests for testing http GET, POST... methods beside the fm.getFiles()... functions
# TODO: uncomment & fix the test for getFileDetails once the function is ready

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
        #       date: "2012-04-05 05:43",
        #       mimetype: "application/x-esri-shp" || "application/octet-stream"
        #   },
        #   ...
        # ]
        
        # NOTE: mimetypes should be handled according to https://portal.opengeospatial.org/files/?artifact_id=47860

        workdir = os.path.abspath(os.path.join(TEST_DIR,"workdir","data"))
        files_json = self.fm.getFiles(workdir)
        import json
        files = json.loads(files_json)

        self.assertEquals(type(files), type([]), "List is an array")
        self.assertEquals(len(files), len(os.listdir(workdir)), "Number of files match")
        self.assertListEqual(files[0].keys(),["date","mimetype", "name", "size"],"File attributes are existing")

#    def test_getFileDetails(self):
#        """Test get file detail request"""

        # example of expected json response:
        # {
        #     name: "file.shp",
        #     size: 1000000,
        #     date: "2012-04-05 05:43",
        #     mimetype: "application/x-esri-shp" || "application/octet-stream"
        #     prj: "epsg:4326",
        #     features: 150,
        #     geomtype: "line",
        #     extent: [10,50,15,55],
        #     attributes: {
        #           "cat": "real",
        #           "rgntyp": "string",
        #           kod": "string",
        #           nazev": "string",
        #           smer": "string",
        #           poityp": "string",
        #           kod_popis": "string"
        #     }
        # },
        # ...
        
        # NOTE: mimetypes should be handled according to https://portal.opengeospatial.org/files/?artifact_id=47860
        # NOTE: shapefile does not have one ... maybe octet-stream

#        workdir = os.path.abspath(os.path.join(TEST_DIR,"workdir","data"))

#        filed = self.fm.getFileDetails("line_crs.shp")
#        self.assertEquals(filed["name"], "line_crs.shp","File name")
#        self.assertEquals(filed["size"], 404,"File size")
#        self.assertEquals(filed["mimetype"], "application/octet-stream","Mime type")
#        self.assertEquals(filed["features"],2,"Number of features")
#        self.assertEquals(filed["prj"], "epsg:4326","Projection")
#        self.assertEquals(filed["geomtype"], "line","Geometry type")
#        self.assertListEqual(filed["extent"], [-1.029182,-0.618030,0.805390,0.748141],"File extent")
#        self.assertDictEqual(filed["attributes"], {"id":"integer"},"Attributes")


if __name__ == "__main__":
   suite = unittest.TestLoader().loadTestsFromTestCase(FileManTestCase)
   unittest.TextTestRunner(verbosity=2).run(suite)
