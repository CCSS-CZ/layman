# Lincense: ...
# authors: Michal, Jachym

import os, sys
#import glob
import mimetypes, time
import json

class FileMan:
    """File manager of LayMan
    """

    config = None

    def __init__(self,config = None):
        """constructor
        """

        ## get configuration parser
        self._setConfig(config)

    #
    # GET methods
    #

    # TODO: Get the proper directory
    # This will be somehow related to the authentication module, 
    # where we need several things specified for every user, 
    # such as FS working directory, GS workspace(s) and DB schema(s) 
    def getFiles(self, dir="tests/workdir/data/"):
        """Get the list of files
            Should return: 
            [
               {
                  name: "file.shp",
                  size: 1000000,
                  date: "2012-04-05 05:43",
                  mimetype: "application/x-esri-shp" || "application/octet-stream"
               },
               ...
             ]
            """

        # ls options
        # http://www.saltycrane.com/blog/2010/04/monitoring-filesystem-python-and-pyinotify/
        #
        # files = os.listdir(dir) # file names only
        # files = os.walk(dir) # file names only, recursive
        # files = glob.glob("/home/mis/layman/server/layman/fileman/*py") # file names only, allows wildcards
        # or run `ls` as a subprocess (platform dependent)

        files_list = []

        filenames = os.listdir(dir) # file names only
        for file in filenames:
            filesize = os.path.getsize(dir+'/'+file)
            time_sec = os.path.getmtime(dir+'/'+file) 
            time_struct = time.localtime(time_sec)
            filetime = time.strftime("%Y-%m-%d %H:%M",time_struct)
            filetype = mimetypes.guess_type("file://"+dir+'/'+file)
            file_dict = {"name":file,"size":filesize,"date":filetime,"mimetype":filetype[0]}           
            files_list.append(file_dict)
                
        files_json = json.dumps(files_list)

        return files_json

    def getFileDetails(self, filename):
        """Get the details for the given file
            Returns:
            {
             name: "file.shp",
             size: 1000000,
             date: "2012-04-05 05:43",
             mimetype: "application/x-esri-shp" || "application/octet-stream"
             prj: "epsg:4326",
             features: 150,
             geomtype: "line",
             extent: [10,50,15,55],
             attributes: {
                   "cat": "real",
                   "rgntyp": "string",
                   "kod": "string",
                   "nazev": "string",
                   "smer": "string",
                   "poityp": "string",
                   "kod_popis": "string"
             }
         }
        """
        return "Will provide the file details of " + filename + " as soon as will know it"

    #
    # POST methods
    #

    def postFile(self,fileName,data):
        """Create a file and return 201 Created.
           Should the file already exist, do nothing and return 409 Conflict
        """
        # is the file already there?
        try:
           with open(fileName) as f: 
               isThere = True
               f.close()
        except IOError as e:
           isThere = False

        # it is there, DO NOT overwrite
        if isThere:
            return "Sorry, the file already exists, use PUT method if you wish to overwrite it" 

        # it is not there, create it
        else:
            f = open(fileName, "wb")
            f.write(data)
            f.close
            # TODO: test the file
            return "OK"

    def putFile(self,fileName,data):
        """Update an existing file. 
           If it does not exist, create it.
        """
        f = open(fileName, "wb")
        f.write(data)
        f.close
        # TODO: test the file
        return "OK"

    def deleteFile(self,fileName):
        """Delete the file"""
        os.remove(fileName) #TODO: test the success
        return "OK"

    def _setConfig(self,config):
        """Get and set configuration files parser
        """
        if config:
            self.config = config
        else:
            from layman import config
            self.config =  config

