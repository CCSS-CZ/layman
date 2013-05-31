# Lincense: ...
# authors: Michal, Jachym

#TODO: class ServerMan, GeoServ, MapServ and DbMan

import os
import json
from gsrest import GsRest
from urlparse import urlparse
import logging
from lxml import etree
from io import BytesIO

from layman.errors import LaymanError

namespaces = {
            "sld":"http://www.opengis.net/sld"
        }

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

    ### LAYERS ###

    def publishFromFile(self, fsDir, dbSchema, gsWorkspace, fileName):
        """ Publish from file with GS Config 
            Group ~ db Schema ~ gs Data Store ~ gs Workspace
        """
        # /path/to/file.shp
        filePath = os.path.realpath( os.path.join( fsDir,fileName) )

        # /path/to/file
        filePathNoExt = os.path.splitext(filePath)[0]

        # file
        fileNameNoExt = os.path.splitext(fileName)[0]

        # TODO - check the GS workspace and create it if it does not exist 
        # if...
        #    createWorkspace(...)

        # Here the Workspace should exist

        # TODO - check the GS data store and create it if it does not exist 
        # if...
        #    createDataStore(...)
        # NOTE: Well, this is not needed if we use gsconfig.py "create_featurestore()" 
        # It would be needed for GS "POST FeatureType" request

        # Here the Data Store should exist
  
        # publish with gsconfig.py
        from gsconfig import GsConfig
        gsc = GsConfig(self.config)
        gsc.createFeatureStore(filePathNoExt, gsWorkspace, dataStoreName = fileNameNoExt)
        logging.info("[LayEd][publish] published layer '%s'"% fileNameNoExt)
        logging.info("[LayEd][publish] in workspace '%s'"% gsWorkspace)

        return self.createStyleForLayer(workspace=gsWorkspace, dataStore=fileNameNoExt, layerName=fileNameNoExt)

    def publish(self, fsUserDir, fsGroupDir, dbSchema, gsWorkspace, fileName):
        """ Main publishing function. Import to PostreSQL and publish in GeoServer.
            Group ~ db Schema ~ gs Data Store ~ gs Workspace
        """
        logParam = "fsUserDir="+fsUserDir+" fsGroupDir="+fsGroupDir+" dbSchema="+dbSchema+" gsWorkspace="+gsWorkspace+" fileName="+fileName
        logging.debug("[LayEd][publish] Params: %s"% logParam)

        # /path/to/file.shp
        filePath = os.path.realpath( os.path.join( fsUserDir,fileName) )

        # /path/to/file
        filePathNoExt = os.path.splitext(filePath)[0]

        # file
        fileNameNoExt = os.path.splitext(fileName)[0]

        # Check the GS workspace and create it if it does not exist 
        self.createWorkspaceIfNotExists(gsWorkspace)

        # Here the Workspace should exist

        # Check the GS data store and create it if it does not exist 
        self.createDataStoreIfNotExists(dbSchema, gsWorkspace)

        # Here the Data Store should exist

        # Import to DB
        from layman.layed.dbman import DbMan
        dbm = DbMan(self.config)
        dbm.importShapeFile(filePath, dbSchema)
        # TODO: check the result
        logging.info("[LayEd][publish] Imported file '%s'"% filePath)
        logging.info("[LayEd][publish] in schema '%s'"% dbSchema)

        # SRS
        from layman.fileman import FileMan
        fm = FileMan(self.config)
        gisAttribs = fm.get_gis_attributes(filePath, {})    
        srs = gisAttribs["prj"]
        logging.debug("[LayEd][publish] SRS: %s"% srs)



        # Publish from DB to GS
        self.createFtFromDb(workspace=gsWorkspace, dataStore=dbSchema, layerName=fileNameNoExt, srs=srs)
        # TODO: check the result
        logging.info("[LayEd][publish] Published layer '%s'"% fileNameNoExt)
        logging.info("[LayEd][publish] in workspace '%s'"% gsWorkspace)

        # Create and assgin new style
        self.createStyleForLayer(workspace=gsWorkspace, dataStore=dbSchema, layerName=fileNameNoExt)
        # TODO: check the result

        return (201, "Layer published")

    # Check the GS workspace and create it if it does not exist 
    def createWorkspaceIfNotExists(self, workspace):

        # Check the workspace
        gsr = GsRest(self.config)
        (head, cont) = gsr.getWorkspace(workspace)
        #print head
        #print cont

        # If it does not exist
        if head["status"] != "200":           

            # Create it
            ws = {}
            ws["workspace"] = {}
            ws["workspace"]["name"] = workspace
            wsStr = json.dumps(ws)
            (head, cont) = gsr.postWorkspaces(data=wsStr)
            #print head
            #print cont

            # If the creation failed
            if head["status"] != "201":
                # Raise an exception
                headStr = str(head)
                message = "LayEd: createWorkspaceIfNotExists(): Cannot create workspace " + workspace + ". Geoserver replied with " + headStr + " and said " + cont
                raise LaymanError(500, message)

    # Check the GS data store and create it if it does not exist 
    # Database schema name is used as the name of the datastore
    def createDataStoreIfNotExists(self, dbSchema, gsWorkspace):
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
            #print "POST Data store"
            #print head
            #print cont

            # If the creation failed
            if head["status"] != "201":
                # Raise an exception
                headStr = str(head)
                message = "LayEd: createDataStoreIfNotExists(): Cannot create Data Store " + dbSchema + ". Geoserver replied with " + headStr + " and said " + cont
                raise LaymanError(500, message)

    def createStyleForLayer(self, workspace, dataStore, layerName):
        """ Create and assign new style for layer. 
        Old style of the layer is cloned into the layer's workspace
        and is assigned to the layer.
        """

        # Get the current style
        gsr = GsRest(self.config)
        (head, cont) = gsr.getLayer(workspace, name=layerName) # GET Layer
        # FIXME: we don't really KNOW the name of the layer. The layer of unsure name was automatically created upon POST FeatureType.
        # TODO: check the result
        layerJson = json.loads(cont)

        currentStyleUrl = layerJson["layer"]["defaultStyle"]["href"]

        # Create new style      
        newStyleUrl = self.cloneStyle(fromStyleUrl=currentStyleUrl, toWorkspace=workspace, toStyle=layerName) 
        logging.info("[LayEd][createStyleForLayer] created style '%s'"% layerName)
        logging.info("[LayEd][createStyleForLayer] in workspace '%s'"% workspace)
        # TODO: check the result
       
        # Assign new style with gsxml
        style_str = {}
        style_str["layer"] = {}
        style_str["layer"]["defaultStyle"] = {}
        style_str["layer"]["defaultStyle"]["name"] = layerName
        style_str["layer"]["defaultStyle"]["workspace"] = workspace
        style_str["layer"]["enabled"] = True

        headers, content = gsr.putLayer(workspace, layerName, json.dumps(style_str))

        logging.info("[LayEd][publish] assigned style '%s'"% layerName)
        logging.info("[LayEd][publish] to layer '%s'"% layerName)
        logging.info("[LayEd][publish] in workspace '%s'"% workspace)
        # TODO: check the result

        # Tell GS to reload the configuration
        gsr.putReload()


    def createFtFromDb(self, workspace, dataStore, layerName, srs):
        """ Create Feature Type from PostGIS database
            Given dataStore must exist in GS, connected to PG schema.
            layerName corresponds to table name in the schema.
        """

        # Create ft json 
        ftJson = {}
        ftJson["featureType"] = {}
        ftJson["featureType"]["name"] = layerName
        ftJson["featureType"]["srs"] = srs
        ftStr = json.dumps(ftJson)

        # PUT Feature Type        
        gsr = GsRest(self.config)
        logging.debug("[LayEd][createFtFromDb] Create Feature Type: '%s'"% ftStr)
        (head, cont) = gsr.postFeatureTypes(workspace, dataStore, data=ftStr)
        logging.debug("[LayEd][createFtFromDb] Response header: '%s'"% head)
        logging.debug("[LayEd][createFtFromDb] Response contents: '%s'"% cont)

        if head["status"] != "201":
            # Raise an exception
            headStr = str(head)
            message = "LayEd: createFtFromDb(): Cannot create FeatureType " + ftStr + ". Geoserver replied with " + headStr + " and said " + cont
            raise LaymanError(500, message)
        return (head, cont)

    def getLayersGsConfig(self, workspace=None): 
        """returns list of layers"""
        # May be we can remove this one
        from gsconfig import GsConfig
        gs = GsConfig()

        code = 200
        layers =  gs.getLayers() # TODO: select only those from the given workspace
        # NOTE: Do we want to get layers or feature types? (two different things in gs)

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
                layer: {...}
                featureType: {...}
            },
            ...
        ]
        """
        logging.debug("[LayEd][getLayers]")
        gsr = GsRest(self.config)
        code = 200

        # GET Layers
        (headers, response) = gsr.getLayers()
        logging.debug("[LayEd][getLayers] GS GET Layers response header: '%s'"% headers)
        logging.debug("[LayEd][getLayers] GS GET Layers response content: '%s'"% response)
        
        # TODO: check the result
        #print "head"
        #print headers
        #print "resp"
        #print response

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
            # TODO: check the response
            layer = json.loads(response)  # Layer from GS

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
                # TODO: chceck the result
                ft = json.loads(response)   # Feature Type              

                # Return both
                bundle = {}   # Layer that will be returned
                bundle["ws"] = ws
                bundle["roleTitle"] = roleTitles[ws]
                bundle["layer"] = layer["layer"]
                bundle["featureType"] = ft["featureType"]
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
        
                    # Return both
                    bundle = {}   # Layer that will be returned
                    bundle["ws"] = ws
                    bundle["roleTitle"] = roleTitles[ws]
                    bundle["layer"] = layer
                    bundle["featureType"] = ft["featureType"]
                    layers.append(bundle)

        layers = json.dumps(layers) # json -> string
        return (code, layers)

    def deleteLayer(self, workspace, layer, schema, deleteStore=False): 
        """Delete the Layer and the Corresponding Feature Type
           deleteStore = whether to delete the underlying data store as well
        """
        logging.debug("[LayEd][deleteLayer]")
        gsr = GsRest(self.config)
        
        # Find the Feature Type
        headers, response = gsr.getLayer(workspace,layer)
        logging.debug("[LayEd][deleteLayer] GET Layer response headers: %s"% headers)
        logging.debug("[LayEd][deleteLayer] GET Layer response content: %s"% response)
        # TODO: check the result
        layerJson = json.loads(response)
        ftUrl = layerJson["layer"]["resource"]["href"]
        logging.debug("[LayEd][deleteLayer] Feature Type URL: %s"% ftUrl)

        # Delete Layer
        headers, response = gsr.deleteLayer(workspace,layer)
        logging.debug("[LayEd][deleteLayer] DELETE Layer response headers: %s"% headers)
        logging.debug("[LayEd][deleteLayer] DELETE Layer response content: %s"% response)
        # TODO: check the result

        # Delete Feature Type
        headers, response = gsr.deleteUrl(ftUrl)
        logging.debug("[LayEd][deleteLayer] DELETE Feature Type response headers: %s"% headers)
        logging.debug("[LayEd][deleteLayer] DELETE Feature Type response content: %s"% response)
        # TODO: check the result

        # Delete Style (we have created it when publishing)
        headers, response = gsr.deleteStyle(workspace, styleName=layer, purge="true")
        logging.debug("[LayEd][deleteLayer] DELETE Style response headers: %s"% headers)
        logging.debug("[LayEd][deleteLayer] DELETE Style  response content: %s"% response)
        # TODO: check the result 

        # Drop Table in PostreSQL
        from layman.layed.dbman import DbMan
        dbm = DbMan(self.config)
        dbm.deleteTable(dbSchema=schema, tableName=layer)

        # Delete Data Store 
        # (this is usefull when dedicated datastore was created when publishing)
        #print "$$$ layer: $$$ " + layer 
        #if deleteStore == True:
        #    headers, response = gsr.deleteDataStore(workspace,layer)
        # FIXME: tohle zlobi nevim proc        

        # TODO: check the result

        # TODO: return st.

    ### LAYER CONFIG ###

    def getLayerConfig(self, workspace, layerName):
        """ This function combines two things together:
        {{Layer}{FeatureType}}, both in json. 
        Type of the return value is string."""
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
        return (200, retval)

    def putLayerConfig(self, workspace, layerName, data):
        """ This function expects two things together:
        {{Layer}{FeatureType}}, both in json.
        Expected type of data is string."""        
        gsr = GsRest(self.config)
        data = json.loads(data) # string -> json

        # TODO: check, that layer.resource.href 
        # is referrencing the proper feature type

        # PUT Feature Type
        featureTypeJson = {}
        featureTypeJson["featureType"] = data["featureType"] # Extract Feature Type
        ftUrl = data["layer"]["resource"]["href"]            # Extract Feature Type URL
        featureTypeString = json.dumps(featureTypeJson)      # json -> string
        headers, response = gsr.putUrl(ftUrl, featureTypeString) # PUT Feature Type
        # TODO: check the reuslt

        # PUT Layer
        layerJson = {}
        layerJson["layer"] = data["layer"]
        layerString = json.dumps(layerJson)
        headers, response = gsr.putLayer(workspace, layerName, layerString)
        # TODO: check the reuslt and return st.

    ### STYLES ###

    def cloneStyle(self, fromStyleUrl, toWorkspace, toStyle):
        """ Create a copy of a style
            returns url (json) of new style
        """
        gsr = GsRest(self.config)

        # url.json -> url.sld
        dotPos = fromStyleUrl.rfind(".") 
        sldUrl = fromStyleUrl[0:dotPos+1] + "sld"
        #print "*** LayEd *** cloneStyle ** "
        #print "sldUrl:"
        #print sldUrl

        # GET style .sld from GS
        (headers, styleSld) = gsr.getUrl(sldUrl)

        if headers["status"] != "200":
            headStr = str(headers)
            message = "LayEd: cloneStyle(): Cannot get style url " + sldUrl + ".  Geoserver replied with " + headStr + " and said " + styleSld
            raise LaymanError(500, message)

        # change style name and title
        sld_as_file = BytesIO(styleSld)
        tree = etree.parse(sld_as_file)
        layer_name_elem = tree.xpath("//sld:NamedLayer/sld:Name",namespaces=namespaces)
        if len(layer_name_elem) > 0:
            layer_name_elem[0].text = "%s" % (toStyle)

        style_name_elem = tree.xpath("//sld:NamedLayer/sld:UserStyle/sld:Name",namespaces=namespaces)
        if len(style_name_elem) > 0:
            style_name_elem[0].text = "%s" % (toStyle)
            tree.xpath("//sld:NamedLayer/sld:UserStyle/sld:Title",namespaces=namespaces)[0].text =  "Style for layer %s:%s" %(toWorkspace, toStyle)

        styleSld = etree.tostring(tree.getroot())

        # Create new style from the sld
        (headers, response) = gsr.postStyleSld(workspace=toWorkspace, styleSld=styleSld, styleName=toStyle)

        if not headers["status"] in ["201","200"]:
            headStr = str(headers)
            message = "LayEd: cloneStyle(): Cannot create style " + toStyle + ".  Geoserver replied with " + headStr + " and said " + response
            raise LaymanError(500, message)

        # return uri of the new style
        import sys
        print >>sys.stderr, headers, response
        location = headers["location"]
        # GS returns 'http://erra.ccss.cz:8080/geoserver/rest/workspaces/hotari/styles.sld/line_crs'
        # fix geoserver mismatch
        sldPos = location.rfind(".sld")
        location = location[0:sldPos] + location[sldPos+4:] + ".json"
        #print "### LOCATION ###"
        #print location
        return location

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

