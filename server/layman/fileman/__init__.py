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
            (name_root, suffix) = os.path.splitext(fn)
            # filter shx, dbf and prj files
            if suffix in (".shx",".dbf",".prj") and\
                    name_root+".shp" in filenames:
                continue
            filesize = os.path.getsize(targetDir+'/'+fn)
            time_sec = os.path.getmtime(targetDir+'/'+fn) 
            time_struct = time.localtime(time_sec)
            filetime = time.strftime("%Y-%m-%d %H:%M",time_struct)
            filetype = mimetypes.guess_type("file://"+targetDir+'/'+fn)
            file_dict = {"name":fn,"size":filesize,"date":filetime,"mimetype":filetype[0]}           
            files_list.append(file_dict)
                
        files_json = json.dumps(files_list)

        return ("ok",files_json)

    def getFile(self,fileName):
        """Return file itself
        """

        # TODO: set propper Content/type
        try:
            return (200,open(fileName).read())
        except:
            return (500, None)

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

         :return: (status, json_structure)
        """

        if os.path.isfile(fileName): 
            time_sec = os.path.getmtime(fileName) 
            time_struct = time.localtime(time_sec)
            filetime = time.strftime("%Y-%m-%d %H:%M",time_struct)

            details = {}
            details["name"] = os.path.split(fileName)[1]
            details["size"] = os.path.getsize(fileName)
            details["date"] = str(filetime)
            details["mimetype"] = mimetypes.guess_type("file://"+fileName)[0]
            # TODO: more to be done

            layerfiles_json = json.dumps(details)

            return ("ok",files_json)
        else:
            return (404,"{success:false,message:'Requested file not found'}")

    #
    # POST methods
    #

    def postFile(self,filePath,data):
        """Create a file and return 201 Created.
           Should the file already exist, do nothing and return 409 Conflict

           :return: (status, response)
        """
            
        fileName = os.path.split(filePath)[-1]

        # it is there, DO NOT overwrite
        if os.path.exists(filePath):

            return ("conflict",
                    "{success:false, message:'Sorry, the file [%s] already exists, use PUT method if you wish to overwrite it'}" % fileName)

        # it is not there, create it
        else:
            try:
                f = open(filePath, "wb")
                f.write(data)
                f.close()
                return ("created","{'success':true, file:'%s'}" % fileName)
            except Exception as e:
                return (internalerror,"{success: false, message: '%s'}" % e.strerror)

    def putFile(self,fileName,data):
        """Update an existing file. 
           If it does not exist, create it.

           :return: (status, response)
        """
        try: 
            f = open(fileName, "wb")
            f.write(data)
            f.close
            return ("ok","{'success':'true','action':'updated'}")
        except Exception as e:
            return (500, "{success: false, message: '%s'}" % e.message)

    def deleteFile(self,fileName):
        """Delete the file"""
        try:
            os.remove(fileName)
            retval = "Deleted"
        except Exception as e:
            retval = e.message

        if os.path.exists(fileName):
            return (500, "{success: false, message: '%s'}" % "Unable to delete file")
        else:
            return ("ok",retval)

    def _setConfig(self,config):
        """Get and set configuration files parser
        """
        if config:
            self.config = config
        else:
            from layman import config
            self.config =  config
