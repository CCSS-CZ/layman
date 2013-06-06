# Lincense: ...
# authors: Michal, Jachym

import os, sys
#import glob
import mimetypes, time
import json
import logging
import zipfile
from osgeo import ogr
from osgeo import gdal
from osgeo import osr

from layman.errors import LaymanError

class FileMan:
    """File manager of LayMan
    """

    config = None
    tempdir = None

    def __init__(self,config = None):
        """constructor
        """

        ## get configuration parser
        self._setConfig(config)

        # create tempdir
        self.tempdir = self.config.get("FileMan","tempdir")
        if not os.path.exists(self.tempdir):
            os.mkdir(self.tempdir)


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
            if suffix in (".shx",".dbf",".prj",".sbn") and\
                    name_root+".shp" in filenames:
                continue
            filesize = os.path.getsize(targetDir+'/'+fn)
            time_sec = os.path.getmtime(targetDir+'/'+fn) 
            time_struct = time.localtime(time_sec)
            filetime = time.strftime("%Y-%m-%d %H:%M",time_struct)
            filetype = self.guess_type(targetDir, fn)
            file_dict = {"name":fn,"size":filesize,"date":filetime,"mimetype":filetype}           
            files_list.append(file_dict)
                
        files_json = json.dumps(files_list)

        return (200, files_json)

    def guess_type(self, target_dir, fn):
        """Gues mimetype
        """
        filetype = mimetypes.guess_type("file://"+target_dir+'/'+fn)
        if filetype[0]:
            return filetype[0]
        else:
            ext = os.path.splitext(fn)[1].lower()

            if ext == ".shp":
                return "application/x-qgis"
            elif ext == ".gml":
                return "application/gml+xml"
            elif ext == ".tiff":
                return "image/tiff"

    def getFile(self,fileName):
        """Return file itself
        """

        # TODO: set propper Content/type
        try:
            return (200, open(fileName).read())

        except Exception as e:
            message = "LayEd: getFile(): Unable to read from the file named '" + fileName + "'. Exception received: " + str(e)
            raise LaymanError(500, message)

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
            details = self.get_gis_attributes(fileName, details)

            files_json = json.dumps(details)

            return (200, files_json)
        else:
            message = "Requested file '" + fileName + "' not found"
            return (404, message)

    #
    # POST methods
    #

    def postFile(self,filePath,data):
        """Create a file and return 201 Created.
           Should the file already exist, do nothing and return 409 Conflict

           :return: (status, response)
        """
            
        logging.debug("FileMan.postFile() filePath: %s"% filePath)

        #fileName = os.path.split(filePath)[-1]

        pathParsed = os.path.split(filePath)
        fileName = pathParsed[-1]
        dirPath = pathParsed[-2]

        logging.debug("FileMan.postFile() pathParsed: %s"% str(pathParsed))
        logging.debug("FileMan.postFile() fileName: %s"% fileName)
        logging.debug("FileMan.postFile() dirPath: %s"% dirPath)

        # make sure that the directory exists
        dirExists = os.path.exists(dirPath) and os.path.isdir(dirPath)
        if not dirExists:
            try:
                os.makedirs(dirPath)
            except Exception as e:
               errMsg = "[FileMan][postFile] Cannot create user directory %s: %s" % (dirPath, str(e))
               logging.error(errMsg)
               raise LaymanError(500, errMsg) 

        # The file is there, DO NOT overwrite
        if os.path.exists(filePath):

            return ("conflict",
                    "Sorry, the file [%s] already exists, use PUT method if you wish to overwrite it" % fileName)

        # The file is not there, create it
        else:
            try:
                f = open(filePath, "wb")
                f.write(data)
                f.close()

                # handle zip files
                msg = None
                if zipfile.is_zipfile(filePath):
                    (fileName,msg) = self._unzipFile(filePath)
                if fileName:
                    logging.info("File [%s] successfully uploaded"% fileName)
                    return ("created","File uploaded:'%s'" % fileName)
                else:
                    logging.error(msg)
                    return ("internalerror","Error while uploading/unzipping file: '%s'" % msg)
            except Exception as e:
                logging.error(e)
                raise LaymanError("internalerror","FileMan: postFile(): %s" % str(e))

    def putFile(self,fileName,data):
        """Update an existing file. 
           If it does not exist, create it.

           :return: (status, response)
        """
        try: 
            f = open(fileName, "wb")
            f.write(data)
            f.close()
            return ("ok","{'success':'true','action':'updated'}")
        except Exception as e:
            return (500, "{success: false, message: '%s'}" % e.message)

    def deleteFile(self,fileName):
        """Delete the file"""
        try:
            (name_root, suffix) = os.path.splitext(fileName)

            if suffix == ".shp":
                self._deleteShapeFile(fileName)
            else:
                os.remove(fileName)

            if os.path.exists(fileName):
                return (500, "{success: false, message: '%s'}" % "Unable to delete file")
            else:
                return (200, "{success: true, message: '%s'}" % "File deleted")

        except Exception as e:
            return (500, "{success: false, message: '%s'}" % e)

    def get_gis_attributes(self,fileName, attrs):
        """Append more gis attributes of given file to attrs hash
        """
        
        # try vector
        ds = ogr.Open(fileName)
        # opening vector success
        if ds:
            attrs = self._get_vector_attributes(ds,attrs)

        # try raster
        else:
            ds = gdal.Open(fileName)

            # opening raster success
            if ds:
                attrs = self._get_raster_attributes( ds,attrs)
            # no gis data
            else:
                pass

        return attrs

    def _get_vector_attributes(self,ds,attrs):

        layer = ds.GetLayer()

        # extent
        extent = layer.GetExtent()
        attrs["extent"] = (extent[0],extent[2],extent[1],extent[3])

        # features count
        attrs["features_count"] = layer.GetFeatureCount()

        # geom type
        ftype = layer.GetGeomType()
        if ftype == ogr.wkbPolygon:    #3
            attrs["type"] = "polygon"
        elif ftype == ogr.wkbPoint:    #1
            attrs["type"] = "point"
        elif ftype == ogr.wkbLineString:   #2
            attrs["type"] = "line"
        elif ftype == ogr.wkbPolygon25D:
            attrs["type"] = "polygon"
        else: 
            attrs["type"] = "none/unknown"  # 0 or anything else

        # srs
        sr = layer.GetSpatialRef()
        if sr:
            sr.AutoIdentifyEPSG()
            attrs["prj"]= self._get_prj(sr)
        else:
            attrs["prj"] = "unknown"

        # Done
        return attrs

    def _get_raster_attributes(self,ds,attrs):
        """Collect raster attributes
        """

        attrs["type"] = "raster"

        geotransform = ds.GetGeoTransform()
        attrs["extent"] = (geotransform[0], 
                           geotransform[3]+(geotransform[5]*ds.RasterYSize), 
                           geotransform[0]+(geotransform[1]*ds.RasterXSize),
                           geotransform[3])

        sr = osr.SpatialReference()
        sr.ImportFromWkt(ds.GetProjectionRef())
        attrs["prj"] = self._get_prj(sr)

        attrs["features_count"] = "%s raster, %dx%d cells" % \
                (ds.RasterCount, ds.RasterXSize, ds.RasterYSize)

        return attrs

    def _get_prj(self,sr):

        if sr.IsGeographic() == 1:  # this is a geographic srs
            cstype = 'GEOGCS'
        else:  # this is a projected srs
            cstype = 'PROJCS'
        an = sr.GetAuthorityName(cstype)
        ac = sr.GetAuthorityCode(cstype)

        return "%s:%s"%(an,ac)


    def _deleteShapeFile(self, fileName):
        """Delete all files, belonging to this shapefile
        """
        (name_root, suffix) = os.path.splitext(fileName)
        (d,root) = os.path.split(name_root)

        for f in os.listdir(d):
            if f.find(root) == 0:
                os.remove(os.path.join(d, f))

    def _setConfig(self,config):
        """Get and set configuration files parser
        """
        if config:
            self.config = config
        else:
            from layman import config
            self.config =  config

    def _unzipFile(self, zfile):
        """Extract shapefiles from zipped file
        """

        (target_dir,target_name) = os.path.split(zfile)
        (target_root,target_suffix) = os.path.splitext(target_name)
        zf  = zipfile.ZipFile(zfile)

        # exctarct zip into temporary location
        zf.extractall(path=self.tempdir)

        files = zf.namelist()
        tempfiles = []
        fileName = None

        # rename files to target location with new name
        for shape_file_part in files:
            (root, suffix) = os.path.splitext(shape_file_part)
            # rename file as desired
            os.rename(os.path.join(self.tempdir,shape_file_part),os.path.join(target_dir,target_root+suffix))
            shape_file_part = target_root+suffix
            tempfiles.append(shape_file_part)
            if suffix == ".shp":
                fileName = shape_file_part

        # remote original zip
        os.remove(zfile)

        # check
        for shape_file_part in files:
            if os.path.exists(os.path.join(self.tempdir, shape_file_part)):
                os.remove(os.path.join(self.tempdir, shape_file_part))

        if not fileName:
            for file_name in tempfiles:
                if os.path.exists(os.path.join(self.tempdir, file_name)):
                    os.remove(os.path.join(self.tempdir, file_name))
            # clear
            return (None, "No shapefile content")
        else:
            return (fileName, "%s unzipped" % zfile)

