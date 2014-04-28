# Lincense: ...
# authors: Michal, Jachym

import os
import json
from urlparse import urlparse
import logging
from lxml import etree
from io import BytesIO
import shutil

from gsrest import GsRest
from gsxml import GsXml
from gssec import GsSec
from layman.errors import LaymanError

namespaces = {
    "sld": "http://www.opengis.net/sld"
}

# Refactor: We may want to split the class in two, 
# the second one would deal with the "Data" panel

# For now, with GeoServer only
# For MapServer, common ancestor should be created
class LayEd:
    """Layer editor and manager
    """

    config = None

    def __init__(self,config = None):
        """constructor
        """

        ## get configuration parser
        self._setConfig(config)

    def _setConfig(self,config):
        """Get and set configuration files parser
        """
        if config:
            self.config = config
        else:
            from layman import config
            self.config =  config

    ### DATA ###

    # Get the list of tables and views in the given schemas
    # For future: Add some other resources (files, WMS)
    def getData(self, roles):
        """ 
            roles:
                [
                    {
                     roleName: hasici,
                     roleTitle: FireMen
                    },
                    {
                     roleName: policajti,
                     roleTitle: Mirabelky
                    }
                ]    

            roleName ~ schema
        """
        from layman.layed.dbman import DbMan
        dbm = DbMan(self.config)
        
        # Map role names to schemas
        schemas = map( lambda r: r["roleName"], roles )

        # Get tables
        tables = dbm.getTables(schemas)
        for t in tables:
            t["type"] = "table"

        # Get views
        views = dbm.getViews(schemas)
        for v in views:
            v["type"] = "view"

        # Concat
        data = tables + views

        # Add the role titles
        # Db doesn't know about role titles. 
        # We map it for client's convenience
        rolemap = {}
        for role in roles:
            rolemap[ role["roleName"] ] = role["roleTitle"] 

        for d in data:
            d["roleTitle"] = rolemap[ d["schema"] ] # roleName ~ schema
            
        code = 200
        retval = json.dumps(data)        
        return (code, retval)

    ### LAYERS ###

    # Import and publish, rasters and vectors
    def importAndPublish(self, fsUserDir, fsGroupDir, dbSchema, gsWorkspace, fileName, srs=None, tsrs=None, data=None, secureLayer=True):
        """ Main publishing function. 
        Vectors import to PostreSQL and publish in GeoServer. 
        Rasters copy to GeoServer datastore dir and publish from there in GS.
            Group ~ db Schema ~ gs Data Store ~ gs Workspace
        """
        logParam = "fsUserDir=%s fsGroupDir=%s dbSchema=%s gsWorkspace=%s fileName=%s" %\
                   (fsUserDir, fsGroupDir, dbSchema, gsWorkspace, fileName)
        logging.debug("[LayEd][importAndPublish] Params: %s"% logParam)

        code = 500
        message = "Strange - message was not set"
        layerName = "NONAME"

        # /path/to/file.shp
        filePath = os.path.realpath( os.path.join(fsUserDir,fileName) )

        # /path/to/file
        filePathNoExt = os.path.splitext(filePath)[0]

        # file
        fileNameNoExt = os.path.splitext(fileName)[0].lower()      

        if srs is None or "none" in srs.lower(): # python uses lazy evaluation
            # Identify the SRS
            from layman.fileman import FileMan
            fm = FileMan(self.config)
            gisAttribs = fm.get_gis_attributes(filePath, {})
            srs = gisAttribs["prj"]
            logging.debug("[LayEd][importAndPublish] Detected SRS: %s" % srs)

            if srs is None or "none" in srs.lower():
                return (500, None, "Cannot detect the SRS. Please specify the SRS.")
            
        else:
            logging.debug("[LayEd][importAndPublish] Using given SRS: %s" % srs)

        if tsrs is None or "none" in tsrs.lower():
            tsrs = srs

        # Identify the data type
        data_type = None
        from osgeo import ogr
        ds = ogr.Open(filePath)

        # Vector
        if ds:
            data_type = "vector"

            # Import vector to PostGIS
            tableName = self.importFromFileToDb(filePath, dbSchema, srs, tsrs)
            
            # Publish from PostGIS to GeoServer
            (code, layerName, message) = self.publishFromDbToGs(dbSchema, tableName, gsWorkspace, tsrs, data, None, None, secureLayer)

        else:
            from osgeo import gdal
            ds = gdal.Open(filePath)

            # Raster
            if ds:
                data_type = "raster"

                # Publish from raster file to GeoServer
                (code, layerName, message) = self.publishRasterToGs(filePath, gsWorkspace, ds, fileNameNoExt, srs, data, None, None, secureLayer)

        if not data_type:
            raise LaymanError(500, "Data type (raster or vector) not recognized")

        return (code, layerName, message)

    def importFromFileToDb(self, filePath, dbSchema, srs, tsrs):
        """ Import data from vector file to PostreSQL 
        If a table of the same name already exists, new table with modified name is created.
        """
        logParam = "filePath=%s dbSchema=%s" %\
                   (filePath, dbSchema)
        logging.debug("[LayEd][importFromFileToDb] Params: %s"% logParam)

        # Import to DB
        from layman.layed.dbman import DbMan
        dbm = DbMan(self.config)
        
        tableName = dbm.importVectorFile(filePath, dbSchema, srs, tsrs)

        logging.info("[LayEd][importFromFileToDb] Imported file '%s'" % filePath)
        logging.info("[LayEd][importFromFileToDb] in schema '%s'" % dbSchema)

        return tableName

    def publishFromDbToGs(self, dbSchema, tableName, gsWorkspace, srs=None, data=None, styleName=None, styleWs=None, secureLayer=True):
        """ Publish vector data from PostGIS to GeoServer.
            A name of a view can be used as a tableName as well.
        """
        logParam = "dbSchema=%s tableName=%s gsWorkspace=%s srs=%s" %\
                   (dbSchema, tableName, gsWorkspace, srs)
        logging.debug("[LayEd][publish] Params: %s"% logParam)

        # Check the GS workspace and create it if it does not exist
        self.createWorkspaceIfNotExists(gsWorkspace)

        # Check the GS data store and create it if it does not exist
        dataStore = self.createVectorDataStoreIfNotExists(dbSchema, gsWorkspace)

        # Publish from DB to GS
        layerName = self.createFtFromDb(gsWorkspace, dataStore, tableName, srs, data, secureLayer)

        # Set attribution of the layer
        self.updateLayerAttribution(gsWorkspace, layerName, data)

        # Create and assgin new style
        self.createStyleForLayer(gsWorkspace, layerName, styleName, styleWs)

        logging.info("[LayEd][publish] Published layer '%s'" % layerName)
        logging.info("[LayEd][publish] in workspace '%s'" % gsWorkspace)

        code = 201
        message = "Layer published: " + layerName
        return (code, layerName, message)

    def publishRasterToGs(self, filePath, gsWorkspace, ds, name, srs=None, data=None, styleName=None, styleWs=None, secureLayer=True):
        """ Publish raster files in GeoServer.
        """
        logParam = "filePath=%s gsWorkspace=%s ds=%s name=%s srs=%s" %\
                   (filePath, gsWorkspace, ds, name, srs)
        logging.debug("[LayEd][publish] Params: %s"% logParam)

        # Check the GS workspace and create it if it does not exist
        self.createWorkspaceIfNotExists(gsWorkspace)

        # Check the GS data store and create it if it does not exist
        # Warning! This function overwrites the file if it was already there
        self.createCoverageStoreIfNotExists(ds, name, gsWorkspace, filePath)

        # Publish from raster file to GS
        layerName = self.createCoverageFromFile(gsworkspace=gsWorkspace,
                                                   store=name,
                                                   name=name,
                                                   srs=srs, data=data, secureLayer=secureLayer)

        # Set attribution of the layer
        self.updateLayerAttribution(gsWorkspace, layerName, data)

        # Create and assgin new style
        self.createStyleForLayer(gsWorkspace, layerName, styleName, styleWs)

        logging.info("[LayEd][publish] Published layer '%s'" % name)
        logging.info("[LayEd][publish] in workspace '%s'" % gsWorkspace)

        return (201, layerName, "Layer published")

    def updateRasterFile(self, gsworkspace, filePath):
        """Just copy raster file to target directory
        """

        data_dir = self.config.get("GeoServer", "datadir")
        ws_data_dir = os.path.join(data_dir, "workspaces", gsworkspace, "data")
        shutil.copy2(filePath, ws_data_dir)
        logging.debug("[LayEd][updateRasterFile]: File %s updated to %s" %
                      (filePath, ws_data_dir))

    def createCoverageStoreIfNotExists(self, ds, name, gsworkspace, filePath):
        """Create CoverageStore in GS if it does not exist yet:
        Create the coverage store dir if it does not exist yet.
        COPY the raster file there - that would overwrite whatever was there!
        """

        # check for data_dir path
        data_dir = self.config.get("GeoServer", "datadir")
        if not data_dir:
            raise LaymanError(500, "Configuration Geoserver/data_dir not set")
        if not os.path.exists(data_dir):
            raise LaymanError(500,
                              "Configured Geoserver/data_dir %s does not exist" %
                              data_dir)

        ws_data_dir = os.path.join(data_dir, "workspaces", gsworkspace, "data")
        # create 'data' directory in the workspace
        if not os.path.exists(ws_data_dir):
            os.mkdir(ws_data_dir)

        shutil.copy2(filePath, ws_data_dir) # overwriting here
        final_name = os.path.join(ws_data_dir, os.path.split(filePath)[1])
        # final check
        if not os.path.exists(final_name):
            raise LaymanError(500, "File seems to be copied into target dir, but not found" % final_name)

        req = {
            "coverageStore":{
                "name": name,
                "type": self._getGSRasterType(ds.GetDriver().ShortName),
                "enabled":"true",
                "workspace":{
                    "name":gsworkspace
                },
                "url":"file:"+final_name,
                "description": "Raster "+name
            }
        }

        dsStr = json.dumps(req)

        # POST
        gsr = GsRest(self.config)
        (head, cont) = gsr.postCoverageStores(gsworkspace, data=dsStr)

        # If the creation failed
        if head["status"] != "201":
            # Raise an exception
            headStr = str(head)
            message = "LayEd: createCoverageStoreIfNotExists(): Cannot create CoverageStore " + final_name + ". Geoserver replied with " + headStr + " and said '" + cont + "'"
            raise LaymanError(500, message)

    def createCoverageFromFile(self, gsworkspace, store, name, srs, data=None, secureLayer=True):

        # Create coverage json
        coverJson = {
            "coverage": {
                "name": name,
                "namespace": {
                    "name":gsworkspace,
                },
                "title":name,
                "description":name,
                "srs": srs,
                "enabled": "true",
                "store": {
                    "class":"coverageStore",
                    "name":store
                }
            }
        }

        if hasattr(data,"title"):
            coverJson["coverage"]["title"] = data["title"]
        if hasattr(data,"abstract"):
            coverJson["coverage"]["description"] = data["abstract"]
            coverJson["coverage"]["abstract"] = data["abstract"]

        coverStr = json.dumps(coverJson)

        gsr = GsRest(self.config)
        logging.debug("[LayEd][createCoverageFromFile] Create Coverage: '%s'"% coverStr)
        (head, cont) = gsr.postCoverage(gsworkspace, store, data=coverStr)
        logging.debug("[LayEd][createCoverageFromFile] Response header: '%s'"% head)
        logging.debug("[LayEd][createCoverageFromFile] Response contents: '%s'"% cont)

        if head["status"] != "201":
            # Raise an exception
            headStr = str(head)
            message = "LayEd: createCoverageFromFile(): Cannot create Coverage " + coverStr + ". Geoserver replied with " + headStr + " and said '" + cont + "'"
            raise LaymanError(500, message)

        # FIXME: return layer name from location header       
        layerName = name

        if secureLayer:

            # Secure the layer (for the native group)
            role = self.secureLayer(gsworkspace, layerName)
    
            # Grant Access (to foreigners)
            
            if hasattr(data, "read_groups"):
                grouplist = map(lambda k: k.strip(), data.read_groups.split(",")) # Groups to be granted from the Client
            else:
                grouplist = []
            if hasattr(data, "read_users"):
                userlist = map(lambda k: k.strip(), data.read_users.split(",")) # Users to be granted from the Client
            else:
                userlist = []

            if gsworkspace not in grouplist:
                grouplist.append(gsworkspace) # Make sure our home group is involved

            self.grantAccess(role, userlist, grouplist)

        return layerName

    # Check the GS workspace and create it if it does not exist
    def createWorkspaceIfNotExists(self, workspace):

        # Check the workspace
        gsr = GsRest(self.config)
        (head, cont) = gsr.getWorkspace(workspace)
        #print head
        #print cont

        # If it does not exist
        if head["status"] != "200":

            # Create and assign the group role
            #
            # Group role controls admin and write access to the workspace
            # and is assigned to the group that owns the worskpace
            #
            # This is done in roles.xml
            #
            gsx = GsXml(self.config)
            groupRole = gsx.createGroupRole(group=workspace)

            # Secure the workspace
            #
            # Set the workspace admin and write access to the group role created above 
            # (Read access will be specified per layer when publishing)
            #
            # This is done in layers.properties
            #           
            from layman.layed.gssec import GsSec
            gss = GsSec(self.config)
            gss.secureWorkspace(ws=workspace, rolelist=[groupRole])

            # Create the workspace
            #
            ws = {}
            ws["workspace"] = {}
            ws["workspace"]["name"] = workspace
            wsStr = json.dumps(ws)
            (head, cont) = gsr.postWorkspaces(data=wsStr)

            # Access Control Note -- Obsolete
            # ===================
            #
            # Here we have created the workspace. Regarding the access control, 
            # this workspace should had been already secured even before it has been created.
            # Setting ws.*.w=ROLE_[group] is done upon a group creation in LR through the LR-LM user if. (liferay-layman user interface)
            # Only after this group has been assigned (that means it has to exist, 
            # that means that securing of the workspace have been already triggered) 
            # a user with such a role can come here.
            #
            # FIXME: If we cancel LR-LM user if (replace by CAS), we need to secure the workspace elsewhere, e.g. here, see gsxml.py: gss.secureWorkspace()
            # -- done as suggested 

            # If the creation failed
            if head["status"] != "201":
                # Raise an exception
                headStr = str(head)
                message = "[LayEd][createWorkspaceIfNotExists] Cannot create workspace " + workspace + ". Geoserver replied with " + headStr + " and said '" + cont + "'"
                raise LaymanError(500, message)

            # Allow WMS
            #
            wms = {}
            wms["wms"] = {}
            wms["wms"]["enabled"] = True
            wmsStr = json.dumps(wms)
            (head, cont) = gsr.putService(service="wms", workspace=workspace, data=wmsStr)

            if head["status"] not in [200, 201]:
                logging.error("[LayEd][createWorkspaceIfNotExists] ERROR enabling WMS. Geoserver replied with %s and said %s" % (head, cont) )

    # Check the GS data store and create it if it does not exist
    # Database schema name is used as the name of the datastore
    def createVectorDataStoreIfNotExists(self, dbSchema, gsWorkspace):
        """Create database connection
        """

        # Check the datastore
        gsr = GsRest(self.config)
        (head, cont) = gsr.getDataStore(workspace=gsWorkspace, name=dbSchema)
        #print "GET Data Store"
        #print head
        #print cont

        # If it does not exist, create it
        if head["status"] != "200":
            # Connection parameters
            host     = self.config.get("DbMan","dbhost")
            port     = self.config.get("DbMan","dbport")
            database = self.config.get("DbMan","dbname")
            user     = self.config.get("DbMan","dbuser")
            passwd   = self.config.get("DbMan","dbpass")
            exposePK = self.config.get("DbMan","exposepk")

            # DataStore JSON
            ds = {}
            ds["dataStore"] = {}
            ds["dataStore"]["name"] = dbSchema # the same name as the schema
            ds["dataStore"]["description"] = "Connection to " + dbSchema + " in the " + database + " PostGIS database."
            ds["dataStore"]["type"] = "PostGIS"
            ds["dataStore"]["connectionParameters"] = {}
            ds["dataStore"]["connectionParameters"]["host"] = host
            ds["dataStore"]["connectionParameters"]["port"] = port
            ds["dataStore"]["connectionParameters"]["database"] = database
            ds["dataStore"]["connectionParameters"]["user"] = user
            ds["dataStore"]["connectionParameters"]["passwd"] = passwd
            ds["dataStore"]["connectionParameters"]["dbtype"] = "postgis"
            ds["dataStore"]["connectionParameters"]["schema"] = dbSchema
            ds["dataStore"]["connectionParameters"]["Expose primary keys"] = exposePK

            dsStr = json.dumps(ds)

            # POST
            (head, cont) = gsr.postDataStores(gsWorkspace, data=dsStr)

            # If the creation failed
            if head["status"] != "201":
                # Raise an exception
                headStr = str(head)
                message = "LayEd: createDataStoreIfNotExists(): Cannot create Data Store " + dbSchema + ". Geoserver replied with " + headStr + " and said '" + cont + "'"
                raise LaymanError(500, message)

            # TODO: return data store name from location header
        
        return dbSchema

    def createStyleForLayer(self, workspace, layerName, styleName=None, styleWs=None):
        """ Create and assign new style for layer.
        Old style of the layer is cloned into a new one and is assigned to the layer.
        New style has a name worskapce_name and is assigned to no worskapce. 
        If styleName is specified, this style is used for cloning instead.
        If the styleName refer to a certain workspace, specify that as styleWs.
        """
        # Do not assign workspace to style. Global GS WMS does not work then.
        # http://sourceforge.net/p/geoserver/mailman/geoserver-users/thread/fb7896e31a0490a0fe3f4cd4f9edfd54@ccss.cz/

        logging.debug("[LayEd][createStyleForLayer] params: workspace %s, layerName %s, styleName %s, styleWs %s" % (workspace, layerName, str(styleName), str(styleWs)))

        gsr = GsRest(self.config)

        # Style not provided - clone the default one that has been automatically assigned to the layer by GeoServer
        if styleName is None or styleName == "":
            logging.debug("[LayEd][createStyleForLayer] GET Layer %s" % layerName)
            (head, cont) = gsr.getLayer(workspace, name=layerName) # GET Layer
            logging.debug("[LayEd][createStyleForLayer] Response header: '%s'" % head)
            logging.debug("[LayEd][createStyleForLayer] Response contents: '%s'" % cont)

            if head["status"] != "200":
                headStr = str(head)
                message = "LayEd: createStyleForLayer(): Cannot get layer to get the current style. Geoserver replied with " + headStr + " and said '" + cont + "'"
                raise LaymanError(500, message)

            layerJson = json.loads(cont)

            fromStyleUrl = layerJson["layer"]["defaultStyle"]["href"]

        # Style given (from no workspace) - use it
        elif styleWs is None or styleWs == "":
            # e.g. http://erra.ccss.cz/geoserver/rest/styles/line.json
            fromStyleUrl = self.config.get("GeoServer","url") + "/styles/" + styleName + ".json"

        # Style given (from some workspace) - use it
        else:
            # Use the given style from some ws
            # e.g. http://erra.ccss.cz/geoserver/rest/workspaces/hasici/styles/pest_02.json
            fromStyleUrl = self.config.get("GeoServer","url") + "/workspaces/" + styleWs + "/styles/" + styleName + ".json"

        # Create new style
        newStyleUrl = self.cloneStyle(fromStyleUrl=fromStyleUrl, toWorkspace=workspace, toStyle=layerName)
        logging.info("[LayEd][createStyleForLayer] created style '%s'"% layerName)
        logging.info("[LayEd][createStyleForLayer] in workspace '%s'"% workspace)

        # Assign new style 
        styleJson = {}
        styleJson["layer"] = {}
        styleJson["layer"]["defaultStyle"] = {}
        styleJson["layer"]["defaultStyle"]["name"] = workspace + "_" + layerName
        styleJson["layer"]["enabled"] = True
        styleStr = json.dumps(styleJson)

        logging.debug("[LayEd][createStyleForLayer] PUT Layer (Assign style): '%s'" % styleStr)
        head, cont = gsr.putLayer(workspace, layerName, styleStr)
        logging.debug("[LayEd][createStyleForLayer] Response header: '%s'" % head)
        logging.debug("[LayEd][createStyleForLayer] Response contents: '%s'" % cont)

        if head["status"] not in ("200", "201"):
            headStr = str(head)
            message = "LayEd: createStyleForLayer(): Cannot assign new syle to the layer. Geoserver replied with " + headStr + " and said '" + cont + "'"
            raise LaymanError(500, message)

        logging.info("[LayEd][publish] assigned style '%s'"% layerName)
        logging.info("[LayEd][publish] to layer '%s'"% layerName)
        logging.info("[LayEd][publish] in workspace '%s'"% workspace)

        # Tell GS to reload the configuration
        gsr.putReload()

    def createFtFromDb(self, workspace, dataStore, tableName, srs, data=None, secureLayer=True):
        """ Create Feature Type from PostGIS database
            Given dataStore must exist in GS, connected to PG schema.
            layerName corresponds to table name in the schema.
        """
        logParam = "workspace=%s dataStore=%s tableName=%s srs=%s" %\
                   (workspace, dataStore, tableName, srs)
        logging.debug("[LayEd][createFtFromDb] Params: %s" % logParam)

        # Create ft json
        ftJson = {}
        ftJson["featureType"] = {}
        ftJson["featureType"]["name"] = tableName
        ftJson["featureType"]["srs"] = srs

        if hasattr(data, "title"):
            ftJson["featureType"]["title"] = data["title"]
        if hasattr(data, "description"):
            ftJson["featureType"]["description"] = data["description"]
            ftJson["featureType"]["abstract"] = data["description"]
        if hasattr(data, "abstract"):
            ftJson["featureType"]["description"] = data["abstract"]
            ftJson["featureType"]["abstract"] = data["abstract"]
        if hasattr(data, "keywords") and data["keywords"] != "":
            ftJson["featureType"]["keywords"] = {}
            ftJson["featureType"]["keywords"]["string"] = \
                map(lambda k: k.strip(), data.keywords.split(","))
        if hasattr(data, "metadataurl") and data["metadataurl"] != "" and data["metadataurl"] != "http://":
            ftJson["featureType"]["metadataLinks"] = {}
            ftJson["featureType"]["metadataLinks"]["metadataLink"] = [
                {
                    'type': "text/xml",
                    'metadataType': 'ISO19115:2003',
                    'content': data.metadataurl
                }
            ]

        ftStr = json.dumps(ftJson)

        # POST Feature Type
        gsr = GsRest(self.config)

        # It can happen that the database is not ready yet when we try to publish a layer
        # So if an attempt fails, give it some time and try it again until some timeout
        import time
        timeout = 120 # time to wait
        sleeptime = 10 # interval between attempts
        for i in range(timeout/sleeptime):

            # post
            logging.debug("[LayEd][createFtFromDb] Create Feature Type: '%s'" % ftStr)
            (head, cont) = gsr.postFeatureTypes(workspace, dataStore, data=ftStr)
            logging.debug("[LayEd][createFtFromDb] Response header: '%s'" % head)
            logging.debug("[LayEd][createFtFromDb] Response contents: '%s'" % cont)
            # head: '{'status': '201', 'content-length': '0', 'vary': 'Accept-Encoding', 'server': 'Noelios-Restlet-Engine/1.0..8', '-content-encoding': 'gzip', 'location': 'http://erra.ccss.cz/geoserver/rest/workspaces/policajti/datastores/policajti/featuretypes.json/pest_00', 'date': 'Wed, 31 Jul 2013 17:49:12 GMT', 'content-type': 'application/json'}'
            # cont: ''

            # if it failed, lets wait
            if head["status"] == "500" and "ransform error" in cont:
                logging.debug("[LayEd][createFtFromDb] Sleeping...")
                time.sleep(sleeptime)
                continue
            else:
                break

        if head["status"] != "201":
            # Raise an exception
            headStr = str(head)
            message = """LayEd: createFtFromDb(): Cannot create FeatureType %s.
                 Geoserver replied with %s and said '%s'""" %\
                      (ftStr, headStr, cont)
            raise LaymanError(500, message)

        # Get location header and extract the name of the layer (== ft name)
        layerName = tableName
        if head["location"] is None:
            logging.warning("[LayEd][createFtFromDb] Got 201 Created Feature Type from GeoServer, but no 'location' header. Assuming layerName == tableName.") 
        else:
            location = head["location"]
            slashPos = location.rfind('/')
            resourceName = location[slashPos+1:]
            dotPos = resourceName.rfind('.')
            if dotPos > -1:
                layerName = resourceName[:dotPos]
            else:
                layerName = resourceName

        if secureLayer:

            # Secure the layer (for the native group) 
            role = self.secureLayer(workspace, layerName)

            # Grant Access (to foreigners)
        
            if hasattr(data, "read_groups"):
                grouplist = map(lambda k: k.strip(), data.read_groups.split(",")) # Groups to be granted from the Client
            else:
                grouplist = []
            if hasattr(data, "read_users"):
                userlist = map(lambda k: k.strip(), data.read_users.split(",")) # Users to be granted from the Client
            else:
                userlist = []

            if workspace not in grouplist:
                grouplist.append(workspace) # Make sure our home group is involved

            self.grantAccess(role, userlist, grouplist)

        return layerName

    def secureLayer(self, workspace, layerName):
        """ Secure read access to the layer. 
        Write and admin access is secured for the whole workspace. 
        Create READ_<ws>_<layer> role and assign it to the group.
        Set <ws>.<layer>.r=READ_<ws>_<layer> in layers.properties.

        It shouldn't matter if the configuration is accidentaly already there.   
        """
        gsx = GsXml(self.config)
        gss = GsSec(self.config)

        # Create READ_<ws>_<layer> role and assign it to the group
        role = gsx.createReadLayerRole(group=workspace, layer=layerName)

        # Set <ws>.<layer>.r=READ_<ws>_<layer>
        gss.secureLayer(ws=workspace, layer=layerName, rolelist=[role])
        
        return role

    def grantAccess(self, role, userlist, grouplist):

        logging.debug("[LayEd][grantAccess] Params: role '%s', userlist '%s', grouplist '%s'"% (str(role), str(userlist), str(grouplist)))

        gsx = GsXml(self.config)        
        gsx.assignRoleToUsersAndGroups(role, grouplist, userlist)

    def updateLayerAttribution(self, workspace, layerName, data=None):
        if data is None: return
        doSt = False # do something

        layerStr = None
        layerJson = {
            "layer": {
                "name": layerName,
                "enabled": True,
                "attribution": {
                }
            }
        }

        if hasattr(data, "attribution_text") and data["attribution_text"] != "":
            layerJson["layer"]["attribution"]["title"] = data.attribution_text
            doSt = True
        if hasattr(data, "attribution_link") and data["attribution_link"] != "" and data["attribution_link"] != "http://":
            layerJson["layer"]["attribution"]["href"] = data.attribution_link
            doSt = True
    
        if not doSt: return

        layerStr = json.dumps(layerJson)

        # PUT Layer
        gsr = GsRest(self.config)                       
        (head, cont) = gsr.putLayer(workspace, layerName, layerStr)
        if head["status"] != "200":
            logging.warning("Set layer attribution failed")

    def getLayersGsConfig(self, workspace=None):
        """returns list of layers"""
        # May be we can remove this one
        from gsconfig import GsConfig
        gs = GsConfig()

        code = 200
        layers =  gs.getLayers() # todo: select only those from the given workspace
        # note: Do we want to get layers or feature types? (two different things in gs)

        return (code,layers)

    def getLayers(self, roles):
        """ Get layers of the given workspaces.

        params:
            roles (json):
            [
               {
                   roleTitle: "User",
                   roleName: "User"
               },
               {
                   roleTitle: "pozarnaja",
                   roleName: "hasici"
               }
            ]
            (can be obtained from Auth.getRoles())

        returns (json encoded as string):
        [
            {
                workspace: "police"
                roleTitle: "Policie Ceske republiky"
                layer: {...}      // geoserver layer object
                layerData: {...}  // geoserver object - featureType, coverage...
            },
            ...
        ]
        """
        logging.debug("[LayEd][getLayers]")
        gsr = GsRest(self.config)
        gsx = GsXml(self.config)
        code = 200

        # GET Layers
        (headers, response) = gsr.getLayers()
        if (not headers['status'] or headers['status'] != '200'):
            logging.debug("[LayEd][getLayers] GS GET Layers response header: '%s'"% headers)
            logging.debug("[LayEd][getLayers] GS GET Layers response content: '%s'"% response)

        if headers["status"] != "200":
            headStr = str(headers)
            message = "[LayEd][getLayers] Get Layers failed. Geoserver replied with " + headStr + " and said: '" + response + "'"
            raise LaymanError(500, message)

        gsLayers = json.loads(response) # Layers from GS

        # Filter ond organise the layers by workspaces
        # For every Layer,
        #   GET Layer,
        #   Check the workspace,
        #   GET FeatureType and
        #   Return both

        layers = []   # Layers that will be returned
        logging.debug("[LayEd][getLayers] Requested workspaces:")

        workspaces = [] # list of workspaces
        roleTitles = {} # roles as dictionary with roleName key
        #print "roles: " + repr(roles)
        for r in roles:
            #print "role: " + repr(r)
            workspaces.append(r["roleName"])
            roleTitles[r["roleName"]] = r["roleTitle"]
            logging.debug("Workspace: %s"% r["roleName"])

        # We also need to check for the duplicities:
        # GS REST is not able to provide list of layers from given workspace.
        # The duplicities in the GET Layers response must be handled manually:
        # 1. Identify the duplicities
        # 2. Insert only once
        # 3. Note all duplicities
        # 4. At the end, come through all the requested workspaces and in every ws check,
        # if it contains the Feature Type of the same name. If yes, add it.
        # Note, that there may be five different layers of the same name in five workspaces
        # and say three allowed for the current user.
        layersDone = {}  # lay[href]: ws
        duplicities = {} # lay[href]: count

        if "layers" in gsLayers:
            if "layer" in gsLayers["layers"]:
                # For every Layer
                for lay in gsLayers["layers"]["layer"]:
                    logging.debug("[LayEd][getLayers] Trying layer '%s'"% lay["href"])
                    #print "Trying layer"
                    #print lay["href"]

                    # Check the duplicities
                    if lay["href"] in layersDone:
                        logging.debug("[LayEd][getLayers] Duplicity found: '%s'"% lay["href"])
                        if lay["href"] in duplicities:
                            duplicities[ lay["href"] ] += 1
                        else:
                            duplicities[ lay["href"] ] = 2
                        continue # dont store the same layer twice
                    else:
                        layersDone[ lay["href"] ] = ""

                    # GET the Layer
                    (headers, response) = gsr.getUrl(lay["href"])
                    # Check the response
                    if headers["status"] != "200":
                        logging.warning("[LayEd][getLayers] Failed to get the Layer. GeoServer replied with '%s' and said '%s'" % (str(headers), str(response)) )
                        continue
                    # Load JSON
                    try:
                        layer = json.loads(response)  # Layer from GS
                    except Exception as e:
                        logging.warning("[LayEd][getLayers] Failed to parse response JSON. GeoServer replied with '%s' and said '%s'" % (str(headers), str(response)) )
                        continue

                    # Check the workspace
                    ftUrl = layer["layer"]["resource"]["href"] # URL of Feature Type
                    urlParsed = urlparse(ftUrl)
                    path = urlParsed[2]                        # path
                    path = [d for d in path.split(os.path.sep) if d] # path parsed
                    if path[2] != "workspaces":                # something is wrong
                        logStr = repr(path)
                        logging.error("[LayEd][getLayers] Strange: path[2] != 'workspaces'. Path: %s"% logStr)
                    ws = path[3]   # workspace of the layer
                    logging.debug("[LayEd][getLayers] Layer's workspace: '%s'"% ws)
                    #print "layer's workspace"
                    #print ws
                    layersDone[ lay["href"] ] = ws
                    if ws in workspaces:

                        # GET FeatureType
                        logging.debug("[LayEd][getLayers] MATCH! Get Feature Type: '%s'"% ftUrl)
                        (headers, response) = gsr.getUrl(ftUrl)
                        #logging.debug("[LayEd][getLayers] ftUrl: %s, headers: %s response: %s" % (str(ftUrl), str(headers), str(response)) )
                        if headers["status"] != "200":
                            logging.warning("[LayEd][getLayers] Failed to get the FeatureType. GeoServer replied with '%s' and said '%s'" % (str(headers), str(response)) )
                            continue
                        try:
                            ft = json.loads(response)   # Feature Type
                        except Exception as e:
                            logging.warning("[LayEd][getLayers] Failed to parse response JSON. GeoServer replied with '%s' and said '%s'" % (str(headers), str(response)) )
                            continue

                        # Learn the groups allowed to read the layer
                        # Corresponds to posession of the role "READ_ws_layerName"
                        # (we get it from roles.xml, not from layers.properties file)
                        readGroups = gsx.getReadLayerGroups(group=ws, layer=str(lay["name"]))

                        # Pack the reply
                        bundle = {}   
                        bundle["ws"] = ws                       # workspace ~ group
                        bundle["roleTitle"] = roleTitles[ws]    # group title
                        bundle["readGroups"] = readGroups       # list of groups allowed to read the layer
                        bundle["layer"] = layer["layer"]        # layer object
                        bundle["layerData"] = {}                # featureType || coverage
                        if "featureType" in ft.keys():
                            bundle["layerData"] = ft["featureType"]
                            #bundle["layerData"]["datatype"] =  "featureType" # this should not be here. 
                            # can be detected from layer[type]. or, if really needed, should be set as bundle[datatype]
                        elif "coverage" in ft.keys():
                            bundle["layerData"] = ft["coverage"]
                            #bundle["layerData"]["datatype"] =  "coverage"
                        layers.append(bundle)

        # Now find the layers hidden by the duplicites

        #print "duplicities"
        #print duplicities
        # For every duplicity
        for (dup, count) in duplicities.items():

            logging.debug("[LayEd][getLayers] Trying duplicity '%s'"% dup)

            # For every requested workspace
            for ws in workspaces:
                if ws == layersDone[ dup ]:
                    continue # this workspace is already done

                # Extract the layer/feature type name
                dotPos = dup.rfind(".")
                slashPos = dup.rfind("/")
                name = dup[slashPos+1:dotPos]

                # Try to get the Feature Type
                # Here we go just for one datastore, the one representing the schema in the db
                (head, resp) = gsr.getFeatureType(workspace=ws, datastore=ws, name=name)

                #print "head status"
                #print head["status"]
                if head["status"] == "200": # match

                    logging.debug("[LayEd][getLayers] Found in workspace '%s'"% ws)

                    ft = json.loads(resp) # Feature Type
                    # Fake layer - valid GS REST URI does not exist
                    layer = {}
                    layer["name"] = name

                    # Learn the groups allowed to read the layer
                    # Corresponds to posession of the role "READ_ws_layerName"
                    readGroups = gsx.getReadLayerGroups(group=ws, layer=str(lay["name"]))

                    # Return both
                    bundle = {}   # Layer that will be returned
                    bundle["ws"] = ws
                    bundle["roleTitle"] = roleTitles[ws]
                    bundle["readGroups"] = readGroups       # list of groups allowed to read the layer
                    bundle["layer"] = layer
                    bundle["layerData"] = {}
                    if "featureType" in ft.keys():
                        bundle["layerData"] = ft["featureType"]
                        bundle["layerData"]["datatype"] = "featureType"
                    if "coverage" in bundle:
                        bundle["layerData"] = ft["coverage"]
                        bundle["layerData"]["datatype"] = "coverage"
                    layers.append(bundle)

        layers = json.dumps(layers) # json -> string
        return (code, layers)

    def deleteLayer(self, workspace, layer, schema, deleteTable):
        """Delete the Layer.
        For vectors, delete the corresponding Feature Type as well.
        For rasters, delete the whole Coverage Store corresponding to the file.
        deleteTable - whether to delete the table with vector data.
        """

        try:
                logging.debug("[LayEd][deleteLayer]")
                gsr = GsRest(self.config)

                # GET Layer
                headers, response = gsr.getLayer(workspace,layer)
                logging.debug("[LayEd][deleteLayer] GET Layer response headers: %s"% headers)
                logging.debug("[LayEd][deleteLayer] GET Layer response content: %s"% response)
                # TODO: check the result
                layerJson = json.loads(response)

                # VECTOR or RASTER
                layer_type = layerJson["layer"]["type"]

                # Resource URL
                resourceUrl = layerJson["layer"]["resource"]["href"]
                logging.debug("[LayEd][deleteLayer] resource (featuretype, coverage...) URL: %s"% resourceUrl)
        
                # Delete Layer
                headers, response = gsr.deleteLayer(workspace,layer)
                logging.debug("[LayEd][deleteLayer] DELETE Layer response headers: %s"% headers)
                logging.debug("[LayEd][deleteLayer] DELETE Layer response content: %s"% response)

                # Delete resource - Feature Type or Coverage
                headers, response = gsr.deleteUrl(resourceUrl)
                logging.debug("[LayEd][deleteLayer] DELETE resource response headers: %s"% headers)
                logging.debug("[LayEd][deleteLayer] DELETE resource response content: %s"% response)

                if layer_type == "VECTOR":
                    # Delete Style (we have created it when publishing)
                    headers, response = gsr.deleteStyle(workspace, styleName=layer, purge="true")
                    logging.debug("[LayEd][deleteLayer] DELETE Style response headers: %s"% headers)
                    logging.debug("[LayEd][deleteLayer] DELETE Style  response content: %s"% response)

                    if deleteTable:
                        # Drop Table/View in PostreSQL
                        from layman.layed.dbman import DbMan
                        dbm = DbMan(self.config)
                        try: # TODO: distnct tables and views once we know it
                            dbm.deleteTable(dbSchema=schema, tableName=layer)
                        except Exception as e:
                            if "DROP VIEW" in str(e):
                                logging.error("[LayEd][deleteLayer] DROP TABLE failed, trying DROP VIEW. Exception was: %s"% str(e))
                                dbm.deleteView(dbSchema=schema, viewName=layer)
                            else:
                                raise e

                elif layer_type == "RASTER":
                    # Delete Coverage Store
                    headers, response = gsr.deleteCoverageStore(workspace,layer)

                # TODO: check the results
                message = "Layer "+workspace+":"+layer+" deleted."
                return (200, message)

        except Exception as e:
           errMsg = "[LayEd][deleteLayer] An exception occurred while deleting layer "+workspace+":"+layer+": "+str(e)
           logging.error(errMsg)
           raise LaymanError(500, errMsg)

        # Delete Data Store
        # (this is usefull when dedicated datastore was created when publishing)
        #print "$$$ layer: $$$ " + layer
        #if deleteStore == True:
        #    headers, response = gsr.deleteDataStore(workspace,layer)
        # FIXME: tohle zlobi nevim proc


    ### LAYER CONFIG ###

    def getLayerConfig(self, workspace, layerName):
        """ This function combines two things together:
        {{Layer}{FeatureType}}, both in json.
        Type of the return value is string."""

        logging.debug("[LayEd][getLayerConfig] GET Layer Config for %s:%s"% (workspace, layerName))

        gsr = GsRest(self.config)

        # GET Layer
        headers, response = gsr.getLayer(workspace, layerName)
        # TODO: check the result
        layerJson = json.loads(response)

        # NOTE: here we assume Feature Type
        # Needs to be extended for Coverages etc.

        # GET Feature Type
        ftUrl = layerJson["layer"]["resource"]["href"]
        headers, response = gsr.getUrl(ftUrl)
        ##print "*** GET CONFIG***"
        ##print headers

        # TODO: check the response
        featureTypeJson = json.loads(response)

        # Return
        retval = {}
        retval["layer"] = layerJson["layer"]
        retval["featureType"] = featureTypeJson["featureType"]
        retval = json.dumps(retval)
        logging.debug("[LayEd][getLayerConfig] Reply with: %s"% (retval))
        return (200, retval)

    def putLayerConfig(self, workspace, layerName, data, fsUserDir,
                       fsGroupDir, dbSchema):
        """ This function expects two things together:
        {{Layer}{FeatureType}}, both in json.
        Expected type of data is string."""

        logging.info("[LayEd][putLayerConfig] PUT Layer Config for %s:%s"% (workspace, layerName))
        logging.info("[LayEd][putLayerConfig] Client requests the following: %s"% (str(data)))

        gsr = GsRest(self.config)

        # Update Data (database or filesystem)

        if "fileName" in data.keys():
            self.updateData(layerName, workspace, fsUserDir, fsGroupDir, dbSchema, data["fileName"])

        # Update Data Settings (geoserver - featureType.xml || coverage.xml)

        layerType = data["layer"]["type"]

        if layerType == "VECTOR":
            # PUT Feature Type
            self.updateFeatureType(data)

        elif layerType == "RASTER":
            # PUT Coverage
            self.updateCoverage(data)
        
        # TODO: PUT WMS Layer
        #elif layerType == "WMS":

        else:
            logging.error("[LayEd][putLayerConfig] Layer %s:%s: Update request for unsupported layer type '%s'"% (workspace, layerName, layerType))
            errMsg = "Cannot update layer settings. Layer type '" + layerType+ "' is not supported."             
            raise LaymanError(500, errMsg)            

        # Update Publishing Settings (geoserver - layer.xml)

        # PUT Layer
        self.updateLayer(workspace, layerName, data)

        # Access Granting (geoserver - roles.xml)

        grouplist = []
        if "readGroups" in data:
            grouplist = map(lambda k: k.strip(), data["readGroups"].split(",")) # Groups to be granted from the Client
            logging.debug("[LayEd][putLayerConfig] Grant access groups: %s"% grouplist)
        else:
            logging.debug("[LayEd][putLayerConfig] No groups provided to grant access")

        userlist = []
        if "readUsers" in data:
            userlist = map(lambda k: k.strip(), data["readUsers"].split(",")) # Users to be granted from the Client
            logging.debug("[LayEd][putLayerConfig] Grant access users: %s"% userlist)
        else:
            logging.debug("[LayEd][putLayerConfig] No users provided to grant access")

        if workspace not in grouplist:
            grouplist.append(workspace) # Make sure our home group is involved

        gsx = GsXml(self.config)
        role = gsx.getReadLayerRoleName(workspace, layerName) # Probably "READ_<ws>_<layer>"

        self.grantAccess(role, userlist, grouplist)

        return (200, "Settings successfully updated")

    # PUT Coverage
    def updateCoverage(self, data):
        logging.debug("[LayEd][updateCoverage] PUT Coverage")

        # Prepare JSON
        coverageJson = {}          
        coverageJson["coverage"] = data["layerData"]
        coverageJson["coverage"]["enabled"] = True # TODO: use previous value. if not specified, gs sets it to false. 
        abstract_text = ""
        if "abstract" in coverageJson["coverage"].keys() and\
                coverageJson["coverage"]["abstract"] != "":
            abstract_text = coverageJson["coverage"]["abstract"]
        elif "description" in coverageJson["coverage"].keys() and\
                coverageJson["coverage"]["description"] != "":
            abstract_text = coverageJson["coverage"]["description"]

        coverageJson["coverage"]["abstract"] = abstract_text
        coverageJson["coverage"]["description"] = abstract_text

        if "keywords" in data.keys() and data["keywords"] != "":
            coverageJson["coverage"]["keywords"] = {}
            coverageJson["coverage"]["keywords"]["string"] = \
                map(lambda k: k.strip(), data["keywords"].split(","))
        if "metadataurl" in data.keys() and data["metadataurl"] != "":
            coverageJson["coverage"]["metadataLinks"] = {}
            coverageJson["coverage"]["metadataLinks"]["metadataLink"] = [
                {
                    'type': "text/xml",
                    'metadataType': 'ISO19115:2003',
                    'content': data["metadataurl"]
                }
            ]

        if "grid" in coverageJson["coverage"]:
            del coverageJson["coverage"]["grid"] # GS doesn't like that

        cvUrl = data["layer"]["resource"]["href"]  # Extract Coverage URL
        coverageString = json.dumps(coverageJson)  # json -> string

        

        # PUT Coverage
        logging.info("[LayEd][putLayerConfig] PUT Coverage: %s"% coverageString)
        gsr = GsRest(self.config)
        (head, cont) = gsr.putUrl(cvUrl, coverageString)

        if head["status"] != "200":
            errorMsg = "Update of data settings failed. "
            logging.error("[LayEd][updateCoverage] PUT Coverage failed. Geoserver replied with '%s' and said: '%s'"% (head, cont))
            raise LaymanError(500, errorMsg)

    # PUT Feature Type
    def updateFeatureType(self, data):
        logging.debug("[LayEd][updateFeatureType] PUT Feature Type")
        
        # Prepare JSON
        featureTypeJson = {}          # Extract Feature Type
        featureTypeJson["featureType"] = data["layerData"]
        featureTypeJson["featureType"]["enabled"] = True # TODO: use previous value. if not specified, gs sets it to false. 
        abstract_text = ""
        if "abstract" in featureTypeJson["featureType"].keys() and\
                featureTypeJson["featureType"]["abstract"] != "":
            abstract_text = featureTypeJson["featureType"]["abstract"]
        elif "description" in featureTypeJson["featureType"].keys() and\
                featureTypeJson["featureType"]["description"] != "":
            abstract_text = featureTypeJson["featureType"]["description"]

        featureTypeJson["featureType"]["abstract"] = abstract_text
        featureTypeJson["featureType"]["description"] = abstract_text

        if "keywords" in data.keys() and data["keywords"] != "":
            featureTypeJson["featureType"]["keywords"] = {}
            featureTypeJson["featureType"]["keywords"]["string"] = \
                map(lambda k: k.strip(), data["keywords"].split(","))
        if "metadataurl" in data.keys() and data["metadataurl"] != "":
            featureTypeJson["featureType"]["metadataLinks"] = {}
            featureTypeJson["featureType"]["metadataLinks"]["metadataLink"] = [
                {
                    'type': "text/xml",
                    'metadataType': 'ISO19115:2003',
                    'content': data["metadataurl"]
                }
            ]
        ftUrl = data["layer"]["resource"]["href"]  # Extract Feature Type URL
        featureTypeString = json.dumps(featureTypeJson)  # json -> string

        # PUT Feature Type
        logging.info("[LayEd][updateFeatureType] PUT Feature Type: %s"% featureTypeString)
        gsr = GsRest(self.config)
        (head, cont) = gsr.putUrl(ftUrl, featureTypeString)

        if head["status"] != "200":
            errorMsg = "Update of data settings failed. "
            logging.error("[LayEd][updateFeatureType] PUT Feature Type failed. Geoserver replied with '%s' and said: '%s'"% (head, cont))
            raise LaymanError(500, errorMsg)

    # PUT Layer
    def updateLayer(self, workspace, layerName, data):
        logging.debug("[LayEd][updateLayer] PUT Layer")

        # Prepare JSON
        layerJson = {}
        layerJson["layer"] = data["layer"]
        layerJson["layer"]["enabled"] = True # TODO: should use previous value
        layerJson["attribution"] = {}
        if "attribution_link" in data.keys() and\
           data["attribution_link"] != "":
            layerJson["layer"]["attribution"]["href"] = \
                data["attribution_link"]
        if "attribution_text" in data.keys() and\
           data["attribution_text"] != "":
            layerJson["layer"]["attribution"]["title"] = \
                data["attribution_text"]
        layerString = json.dumps(layerJson)

        # PUT Layer
        logging.info("[LayEd][updateLayer] PUT Layer %s: %s"% (layerName, layerString))
        gsr = GsRest(self.config)
        (head, cont) = gsr.putLayer(workspace, layerName, layerString)

        if head["status"] != "200":
            errorMsg = "Data settings have been updated succesfully, but the update of publishing settings failed. "
            logging.error("[LayEd][updateLayer] PUT Layer failed. Geoserver replied with '%s' and said: '%s'"% (head, cont))
            raise LaymanError(500, errorMsg)

    def updateData(self, layerName, workspace, fsUserDir, fsGroupDir,
                   dbSchema, fileName):
        """Update data - database or file system -
           from new shape or raster file
        """

        filePath = os.path.realpath(os.path.join(fsUserDir, fileName))

        from osgeo import ogr
        ds = ogr.Open(filePath)
        data_type = None

        # VECTOR
        if ds:

            # Import to DB
            from layman.layed.dbman import DbMan
            dbm = DbMan(self.config)
            dbm.updateVectorFile(filePath, dbSchema, layerName)
            data_type = "vector"

        # RASTER
        else:
            from osgeo import gdal
            ds = gdal.Open(filePath)
            if ds:
                self.updateRasterFile(workspace, filePath)
                data_type = "raster"
                return

        if not data_type:
            raise LaymanError(500,
                              "Data type (raster or vector) not recognized")

    ### STYLES ###

    def cloneStyle(self, fromStyleUrl, toWorkspace, toStyle):
        """ Create a copy of a style
            returns url (json) of new style
            New style is called workspace_name and is assigned to no workspace.
        """
        
        # Do not assign workspace to a style. Global GS WMS does not work then.
        # http://sourceforge.net/p/geoserver/mailman/geoserver-users/thread/fb7896e31a0490a0fe3f4cd4f9edfd54@ccss.cz/
              
        layerName = toStyle
        toStyle = toWorkspace + '_' + toStyle
 
        gsr = GsRest(self.config)

        # url.json -> url.sld
        dotPos = fromStyleUrl.rfind(".")
        sldUrl = fromStyleUrl[0:dotPos+1] + "sld"

        # GET style .sld from GS
        (headers, styleSld) = gsr.getUrl(sldUrl)

        if headers["status"] != "200":
            headStr = str(headers)
            message = "LayEd: cloneStyle(): Cannot get style url " + sldUrl + ".  Geoserver replied with " + headStr + " and said " + styleSld
            raise LaymanError(500, message)

        # change style name and title
        sld_as_file = BytesIO(styleSld)
        try:
            tree = etree.parse(sld_as_file)
        except Exception as e:
            logging.error("[LayEd][cloneStyle] Cannot parse SLD: '%s'. Exception caught: '%s' "% (repr(sld_as_file), e))
            message = "LayEd: cloneStyle(): Cannot parse default SLD"
            raise LaymanError(500, message)

        #layer_name_elem = tree.xpath("//sld:NamedLayer/sld:Name",namespaces=namespaces)
        #if len(layer_name_elem) > 0:
        #    layer_name_elem[0].text = "%s" % (layerName)

        #style_name_elem = tree.xpath("//sld:NamedLayer/sld:UserStyle/sld:Name",namespaces=namespaces)
        #if len(style_name_elem) > 0:
        #    style_name_elem[0].text = "%s" % (toStyle)

        #title_elem = tree.xpath("//sld:NamedLayer/sld:UserStyle/sld:Title",namespaces=namespaces)
        #if len(title_elem) > 0:
        #    title_elem[0].text = "Style for layer %s:%s" %(toWorkspace, layerName)

        styleSld = etree.tostring(tree.getroot())

        # Create new style from the sld
        logging.debug("[LayEd][cloneStyle] Going to create style. SLD: \"%s\" "% styleSld)            
        (headers, response) = gsr.postStyleSld(workspace=None, styleSld=styleSld, styleName=toStyle)

        if not headers["status"] in ["201","200"]:
            logging.error("[LayEd][cloneStyle] This SLD failed: \"%s\" "% styleSld)            
            headStr = str(headers)
            message = "LayEd: cloneStyle(): Cannot create style " + toStyle + ".  Geoserver replied with " + headStr + " and said " + response
            raise LaymanError(500, message)

        # return uri of the new style
        location = headers["location"]
        # GS returns 'http://erra.ccss.cz:8080/geoserver/rest/workspaces/hotari/styles.sld/line_crs'
        # fix geoserver mismatch
        sldPos = location.rfind(".sld")
        location = location[0:sldPos] + location[sldPos+4:] + ".json"
        return location

    def _getGSRasterType(self,rtype):
        """Returns raster type name for geoserver, based on gdal driver name
        """

        if rtype == "GTiff":
            return "GeoTIFF"

    ### WORKSPACES ###

    def getWorkspaces(self): # TODO
        """json of workspaces, eventually with layers"""
        return (501, "I am sorry, not implemented yet")

    def addWorkspace(self,name,attributes=None):
        """create workspace""" #TODO
        return (501, "I am sorry, not implemented yet")

    def removeWorkspace(self,name):
        """remove workspace""" #TODO
        return (501, "I am sorry, not implemented yet")

    def updateWorkspace(self, name,attributes=None):
        """updates existing worspace""" #TODO
        return (501, "I am sorry, not implemented yet")

