# Lincense: ...
# authors: Michal, Jachym

import os, sys
import shutil
#import glob
import mimetypes, time
import json
import logging
import zipfile
from osgeo import ogr
from osgeo import gdal
from osgeo import osr
import web

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
    def getFiles(self, targetDir):
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
        logging.debug("[FileMan][getFiles]")
 
        # Make sure that the user directory exists
        if not os.path.exists(targetDir):
            os.makedirs(targetDir)

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
            # hide shapefile auxiliary files
            if suffix in (".shx",".dbf",".prj",".sbn", ".cpg", ".sbx", ".gvl", ".lyr", ".qpj") and\
                    name_root+".shp" in filenames:
                continue
            # hide mapinfo auxiliary files
            if suffix in (".dat", ".id", ".ind", ".map", "") and\
                    name_root+".tab" in filenames:
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
        #logging.debug("[FileMan][guess_type]")
        
        fileToGuess = "file://"+target_dir+'/'+fn
        retval = "" # mimetype

        filetype = mimetypes.guess_type(fileToGuess)
        if filetype[0]:
            logging.debug("[FileMan][guess_type] File %s recognised as %s."% (fileToGuess, filetype[0]))
            retval = filetype[0]
        else:
            ext = os.path.splitext(fn)[1].lower()
            logging.debug("[FileMan][guess_type] File %s not recognised. Extension: %s "% (fileToGuess, ext))

            if ext == ".shp":
                retval = "application/x-qgis"
            elif ext == ".gml":
                retval = "application/gml+xml"
            elif ext == ".tiff":
                retval = "image/tiff"
            elif ext == ".tab":
                retval = "application/x-mapinfo"

        logging.debug("[FileMan][guess_type] For file %s returning mime type of '%s'."% (fileToGuess, retval))
        return retval

    def getFile(self,fileName):
        """Return file itself
        """

        # TODO: set propper Content/type
        try:
            if fileName.find(".shp") or fileName.find(".tab"):
                (path,fn) = os.path.split(fileName)
                old_path = os.path.abspath(os.path.curdir)
                os.chdir(path)
                fn_noext = os.path.splitext(fn)[0]
                from zipfile import ZipFile
                from io import BytesIO
                filelike = BytesIO()
                zipout = ZipFile(filelike,"w")
                for f in os.listdir(os.path.curdir):
                    if f.find(fn_noext) > -1:
                        zipout.write(f)

                zipout.close()
                web.header('Content-Disposition','attachment; filename="%s.zip"'% fn_noext)
                os.chdir(old_path)
                fn_noext = os.path.splitext(fn)[0]
                return (200, filelike.getvalue())
            else:
                return (200, open(fileName).read())

        except Exception as e:
            message = "LayEd: getFile(): Unable to read from the file named '" + fileName + "'. Exception received: " + str(e)
            raise LaymanError(500, message)

    def getFileDetails(self, fileName):
        """Get the details for the given file
            Returns:
            {
             name: "file.shp"GzipFile,
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

        logging.debug("[FileMan][postFile] pathParsed: %s"% str(pathParsed))
        logging.debug("[FileMan][postFile] fileName: %s"% fileName)
        logging.debug("[FileMan][postFile] dirPath: %s"% dirPath)

        # make sure that the directory exists
        dirExists = os.path.exists(dirPath) and os.path.isdir(dirPath)
        if not dirExists:
            try:
                os.makedirs(dirPath)
                logging.info("[FileMan][postFile] Created user directory: %s"% dirPath)
            except Exception as e:
               errMsg = "[FileMan][postFile] Cannot create user directory %s: %s" % (dirPath, str(e))
               logging.error(errMsg)
               raise LaymanError(500, errMsg) 

        # The file is there, DO NOT overwrite
        # WRONG - filePath is .zip - and that does not exist...
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
                else:
                    # replace special characters in the filename
                    # we allow only letters, numbers, underscore and dot
                    import re
                    newFileName = re.sub('[^a-zA-Z0-9_.]', '_', fileName)
                    if newFileName != fileName:
                        newFilePath = os.path.join(dirPath, newFileName)
                        shutil.move(filePath, newFilePath)
                        
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
            return (200,"PUT File OK")
        except Exception as e:
            errMsg = "PUT File failed: " + str(e)
            return (500, errMsg)

    def deleteFile(self,fileName):
        """Delete the file"""
        try:
            (name_root, suffix) = os.path.splitext(fileName)

            if suffix == ".shp" or suffix == ".tab":
                self._deleteShpTabFiles(fileName)
            else:
                os.remove(fileName)

            if os.path.exists(fileName):
                msg = "Unable to delete file '"+fileName+"'"
                return (500, msg)
            else:
                return (200, "File deleted")

        except Exception as e:
           errMsg = "[FileMan][deleteFile] An exception occurred while deleting file "+fileName+": "+str(e) 
           logging.error(errMsg)
           raise LaymanError(500, errMsg) 

    def get_gis_attributes(self,fileName, attrs):
        """Append more gis attributes of given file to attrs hash
        """
        logging.debug("[FileMan][get_gis_attributes] Params: fileName: %s, attrs: %s" % (fileName, repr(attrs)) )       
 
        # try vector
        ds = ogr.Open(fileName)
       
        # opening vector success
        if ds:
            logging.debug("[FileMan][get_gis_attributes] ogr.Open() O.K" )
            attrs = self._get_vector_attributes(ds,attrs)
            logging.debug("[FileMan][get_gis_attributes] Identified VECTOR attributes: %s" % repr(attrs) )       

        # try raster
        else:
            logging.debug("[FileMan][get_gis_attributes] ogr.Open() Failed" )
            ds = gdal.Open(fileName)

            # opening raster success
            if ds:
                logging.debug("[FileMan][get_gis_attributes] gdal.Open() O.K." )
                attrs = self._get_raster_attributes( ds,attrs)
                logging.debug("[FileMan][get_gis_attributes] Identified RASTER attributes: %s" % repr(attrs) )       
            # no gis data
            else:
                logging.debug("[FileMan][get_gis_attributes] gdal.Open() Failed" )
                logging.debug("[FileMan][get_gis_attributes] No attributes identified for file %s" % fileName )       

        return attrs

    def _get_vector_attributes(self,ds,attrs):
        logging.debug("[FileMan][_get_vector_attributes]")
        
        layer = ds.GetLayer()

        # extent
        extent = layer.GetExtent()
        logging.debug("[FileMan][_get_vector_attributes] Extent: %s" % repr(extent) )
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
        logging.debug("[FileMan][_get_vector_attributes] Spatial Reference from layer.GetSpatialRef() : %s" % repr(sr) )
        if sr:
            sr.AutoIdentifyEPSG()
            logging.debug("[FileMan][_get_vector_attributes] Spatial Reference after sr.AutoIdentifyEPSG() : %s" % repr(sr) )
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
        logging.debug("[FileMan][_get_prj]")

        # Hack for epsg:3857
        hackStr = sr.ExportToProj4()
        if hackStr == '+proj=merc +lon_0=0 +k=1 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs ':
            return "EPSG:3857"
        if hackStr == '+proj=merc +lon_0=0 +k=1 +x_0=0 +y_0=0 +a=6378137 +b=6378137 +units=m +no_defs ':
            return "EPSG:3857"

        if sr.IsGeographic() == 1:  # this is a geographic srs
            logging.debug("[FileMan][_get_prj] Geographic SRS")
            cstype = 'GEOGCS'
        else:  # this is a projected srs
            logging.debug("[FileMan][_get_prj] Projected SRS")
            cstype = 'PROJCS'
        an = sr.GetAuthorityName(cstype)
        ac = sr.GetAuthorityCode(cstype)
        logging.debug("[FileMan][_get_prj] Authority name: %s, Authority code: %s" % (an, ac) )

        return "%s:%s"%(an,ac)

    def _deleteShpTabFiles(self, fileName):
        """Delete all files, belonging to this shapefile or mapinfo
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
        """Extract zipped files
        """
        
        logging.debug("[FileMan][_unzipFile] zfile=%s" % repr(zfile))


        (target_dir,target_name) = os.path.split(zfile)
        (target_root,target_suffix) = os.path.splitext(target_name)
        zf  = zipfile.ZipFile(zfile)


        # exctarct zip into temporary location
        zf.extractall(path=self.tempdir)

        files = zf.namelist()
        logging.debug("[FileMan][_unzipFile] Zip file contents: %s" % str(files))
        tempfiles = []
        fileName = None

        removeDirs = []

        # rename files to target location with new name
        for shape_file_part in files:
            logging.debug("[FileMan][_unzipFile] Loop START")
            (root, suffix) = os.path.splitext(shape_file_part)
          
            target_root = root # don't rename, leave the original name

            # flat the directories
            # Rails/jhmd rails.cpg => Rails_jhmd_rails.cpg
            target_root = "_".join(target_root.split(os.sep))

            # replace special characters
            # we allow only letters, numbers, underscore and dot
            import re
            target_root = re.sub('[^a-zA-Z0-9_.]', '_', target_root)

            # limit the length
            target_root = target_root[-36:]

            logging.debug("[FileMan][_unzipFile] tempdir=%s, shape_file_part=%s, target_dir=%s, target_root=%s, suffix=%s" % (self.tempdir, shape_file_part, target_dir, target_root, suffix))

            suffix = suffix.lower()

            renameFrom = os.path.join(self.tempdir,shape_file_part)
            renameTo = os.path.join(target_dir,target_root+suffix)
            logging.debug("[FileMan][_unzipFile] renameFrom: %s, renameTo: %s" % (renameFrom, renameTo))
    
            # Don't move the directories
            if os.path.isdir(renameFrom):
                logging.debug("[FileMan][_unzipFile] Skipping directory %s" % renameFrom)
                removeDirs.append(renameFrom)
                continue

            shutil.move(renameFrom, renameTo)
            # os.rename(renameFrom, renameTo)

            shape_file_part = target_root+suffix
           
            logging.debug("[FileMan][_unzipFile] Going to append %s" % shape_file_part) 
            tempfiles.append(shape_file_part)
            if suffix == ".shp" or ".tab":
                fileName = shape_file_part
            logging.debug("[FileMan][_unzipFile] Loop END")

        # remove dirs
        for d in removeDirs:
            try:
                shutil.rmtree(d)
            except Exception as e:
                logging.warning("[FileMan][_unzipFile] Remove tree %s raises an exception: %s" % (str(d), str(e)))

        # remove original zip
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
            return (None, "No shapefile or mapinfo content") # do we need that??
        else:
            return (fileName, "%s unzipped" % zfile)

