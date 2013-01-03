# Lincense: ...
# authors: Michal, Jachym

import os, sys
#import glob
import mimetypes, time
import json
import web

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
    def getFiles(self,targetDir):
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

            based on working directory, given by interal authorization
            """

        # ls options
        # http://www.saltycrane.com/blog/2010/04/monitoring-filesystem-python-and-pyinotify/
        #
        # files = os.listdir(dir) # file names only
        # files = os.walk(dir) # file names only, recursive
        # files = glob.glob("/home/mis/layman/server/layman/fileman/*py") # file names only, allows wildcards
        # or run `ls` as a subprocess (platform dependent)

        files_list = []

        filenames = os.listdir(targetDir) # file names only

        for fn in filenames: # NOTE: do not use 'file' variable name - it is
                               # python function
                               # do note use 'dir' - it is another function
            filesize = os.path.getsize(targetDir+'/'+fn)
            time_sec = os.path.getmtime(targetDir+'/'+fn) 
            time_struct = time.localtime(time_sec)
            filetime = time.strftime("%Y-%m-%d %H:%M",time_struct)
            filetype = mimetypes.guess_type("file://"+targetDir+'/'+fn)
            file_dict = {"name":fn,"size":filesize,"date":filetime,"mimetype":filetype[0]}           
            files_list.append(file_dict)
                
        files_json = json.dumps(files_list)

        web.header('Content-Type', 'text/html')
        web.ok() # 200
        return files_json

    def getFile(self,fileName):
        """Return file itself
        """

        # TODO: set propper Content/type
        return open(fileName).read()

    def getFileDetails(self, fileName):
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
        web.ok() # 200

        time_sec = os.path.getmtime(fileName) 
        time_struct = time.localtime(time_sec)
        filetime = time.strftime("%Y-%m-%d %H:%M",time_struct)

        details = {}
        details["name"] = os.path.split(fileName)[1]
        details["size"] = os.path.getsize(fileName)
        details["date"] = str(filetime)
        details["mimetype"] = mimetypes.guess_type("file://"+fileName)[0]
        # TODO: more to be done

        files_json = json.dumps(details)
        web.header('Content-Type', 'text/html')

        return files_json

    #
    # POST methods
    #

    def postFile(self,data,fileName=None):
        """Create a file and return 201 Created.
           Should the file already exist, do nothing and return 409 Conflict
        """

        # it is there, DO NOT overwrite
        if os.path.exists(fileName):
            web.conflict() # 409
            return "Sorry, the file already exists, use PUT method if you wish to overwrite it" 

        # it is not there, create it
        else:
            try:
                f = open(fileName, "wb")
                f.write(data)
                f.close
                web.created() # 201
                return "Created"
            except Exception as e:
                web.internalerror() #500
                return e.message

    def putFile(self,fileName,data):
        """Update an existing file. 
           If it does not exist, create it.
        """
        try: 
            f = open(fileName, "wb")
            f.write(data)
            f.close
            web.ok() # 200
            return "Updated"
        except Exception as e:
            web.internalerror() #500
            return e.message

    def deleteFile(self,fileName):
        """Delete the file"""
        try:
            os.remove(fileName)
            retval = "Deleted"
        except Exception as e:
            retval = e.message

        if os.path.exists(fileName):
            web.internalerror() # 500
            return "Unable to delete file"
        else:
            web.ok() # 200
            return retval

    def _setConfig(self,config):
        """Get and set configuration files parser
        """
        if config:
            self.config = config
        else:
            from layman import config
            self.config =  config
