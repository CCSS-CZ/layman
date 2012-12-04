# Lincense: ...
# authors: Michal, Jachym

import os, sys

class FileMan:
    """File manager of LayMan
    """

    config = None

    def __init__(self,config = None):
        """constructor
        """

        ## get configuration parser
        self._setConfig(config)

    def getFiles(self, dir="."):
        """Get the list of files
            Returns: 
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
        # TODO: how to get the proper directory? 

        
        # Open a file
        # path = "/var/www/html/"
        # dirs = os.listdir( path )

        # This would print all the files and directories
        # for file in dirs:
        #   print file


        return "Will provide the list of files as soon as will know it"

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
        return "Will provide the file details as soon as will know it"

    def _setConfig(self,config):
        """Get and set configuration files parser
        """
        if config:
            self.config = config
        else:
            from layman import config
            self.config =  config

