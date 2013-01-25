import os,sys
import unittest
import ConfigParser

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
INSTALL_DIR = os.path.abspath(os.path.join(TEST_DIR,".."))
sys.path.append(os.path.join(INSTALL_DIR))

# TODO: add tests for testing http GET, POST... methods beside the fm.getFiles()... functions
# TODO: uncomment & fix the test for getFileDetails once the function is ready

from layman.fileman import FileMan

class FileManTestCase(unittest.TestCase):
    """Test of the file manager"""

    fm = None
    workdir = None

    def setUp(self):
        cfg = ConfigParser.SafeConfigParser()
        cfg.read((os.path.join(TEST_DIR,"tests.cfg")))
        cfg.set("FileMan","testdir",TEST_DIR)
        self.fm = FileMan(cfg)

        self.workdir = os.path.abspath(os.path.join(TEST_DIR,"workdir","data"))

    def test_getDir(self):
        """Test dir"""

        self.assertTrue(os.path.samefile(self.workdir, self.fm.config.get("FileMan","targetdir")),
            "Make sure, that configuration works and that the data dir was found")

    def test_getFiles(self):
        """Test get files function"""

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

        (code, files_json) = self.fm.getFiles(self.workdir)
        import json
        files = json.loads(files_json)

        self.assertEquals(type(files), type([]), "List is not an array")
        self.assertEquals(len(files), len(os.listdir(self.workdir)), "Number of files does not match")
        self.assertListEqual(files[0].keys(),["date","mimetype", "name", "size"],"File attributes are not as expected")

    def test_postFile(self):
        """ Test post file function """

        file_path = self.workdir + "punk.sk"

        #make sure the testing file does not exist
        import os
        if os.path.exists(file_path):
            os.remove(file_path)

        """ Test the creation when the file does not exist """
        self.assertEquals(os.path.exists(file_path), False, "The file already exists")
        self.fm.postFile(file_path,"Slobodna Europa")
        self.assertEquals(os.path.exists(file_path), True, "The file was not created")
        f = open(file_path, "rb")
        self.assertEquals(f.read(), "Slobodna Europa", "The file has different content")
        f.close

        """ Test that postFile() does not overwrite the file """
        self.assertEquals(os.path.exists(file_path), True, "The file is not there for the second test")
        self.fm.postFile(file_path,"Zona A")
        f = open(file_path, "rb")
        self.assertEquals(f.read(), "Slobodna Europa", "The file was overwritten by postFile()")

        # clean up
        os.remove(file_path)

    def test_putFile(self):
        """ Test put file function """

        file_path = self.workdir + "punk.sk"

        #make sure the testing file does not exist
        import os
        if os.path.exists(file_path):
            os.remove(file_path)
        
        """ Test the creation when the file does not exist """
        self.assertEquals(os.path.exists(file_path), False, "The file already exists")
        self.fm.putFile(file_path, "Slobodna Europa")
        self.assertEquals(os.path.exists(file_path), True, "The file was not created")
        f = open(file_path, "rb")
        self.assertEquals(f.read(), "Slobodna Europa", "The file has different content")
        f.close

        """ Test that putFile() does overwrite the file """
        self.assertEquals(os.path.exists(file_path), True, "The file is not there for the second test")
        self.fm.putFile(file_path, "Zona A")
        f = open(file_path, "rb")
        self.assertEquals(f.read(), "Zona A", "The file was not overwritten by putFile()")

        # clean up
        os.remove(file_path)

    def test_deleteFile(self):
        """ Test delete file function """

        file_path = self.workdir + "punk.sk"
        open(file_path, "a").close()

        self.assertEquals(os.path.exists(file_path), True, "The testing file does not exist")
        self.fm.deleteFile(file_path)
        self.assertEquals(os.path.exists(file_path), False, "The file was not deleted")

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
