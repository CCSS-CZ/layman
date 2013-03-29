# Lincense: ...
# authors: Michal, Jachym

#TODO: class ServerMan, GeoServ, MapServ and DbMan

import os
import json
from gsrest import GsRest
from urlparse import urlparse

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

    def publish(self, fsDir, dbSchema, gsWorkspace, fileName):
        """ Main publishing function. 
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
   
        from gsconfig import GsConfig
        gs = GsConfig(self.config)
        gs.createFeatureStore(filePathNoExt, gsWorkspace, dataStoreName = fileNameNoExt)
        return fileNameNoExt

    def getLayersGsConfig(self, workspace=None): 
        """returns list of layers"""
        # May be we can remove this one
        from gsconfig import GsConfig
        gs = GsConfig()

        code = 200
        layers =  gs.getLayers() # TODO: select only those from the given workspace
        # NOTE: Do we want to get layers or feature types? (two different things in gs)

        return (code,layers)

    def getLayers(self, workspaces):
        """ Get layers of the given workspaces.        

        params: 
            workspaces (list):
            [ws1, ws2, ws3...]
            (can be obtained from Auth.getRoles())

        returns (json encoded as string):
        {
            ws1: [
                {{Layer}{FeatureType}},
                {{Layer}{FeatureType}},
                ...
            ],
            ws2: [
            ],
            ...
        }
        """
        gsr = GsRest(self.config)
        code = 200

        # GET Layers
        (headers, response) = gsr.getLayers()
        # TODO: check the result
        # print "*** LAYED *** getLayers() ***"
        # print 'gsr.getLayers()'
        # print gsr.getLayers()

        gsLayers = json.loads(response) # Layers from GS

        # Filter ond organise the layers by workspaces
        # For every Layer,
        #   GET Layer,
        #   Check the workspace,
        #   GET FeatureType and
        #   Return both

        layers = {}   # Layers that will be returned
        for ws in workspaces:
            layers[ws] = []

        # For every Layer        
        for lay in gsLayers["layers"]["layer"]: 

            # GET the Layer
            (headers, response) = gsr.getUrl(lay["href"])
            # TODO: check the response
            layer = json.loads(response)  # Layer from GS

            # Check the workspace
            ftUrl = layer["layer"]["resource"]["href"] # URL of Feature Type
            urlParsed = urlparse(ftUrl)                
            path = urlParsed[2]                        # path
            path = [d for d in path.split(os.path.sep) if d] # path parsed
            if path[2] != "workspaces":                
                pass # TODO                            # something is wrong
            ws = path[3]   # workspace of the layer 
            if ws in workspaces:

                # GET FeatureType
                (headers, response) = gsr.getUrl(ftUrl)
                # TODO: chceck the result
                ft = json.loads(response)   # Feature Type              

                # Return both
                bundle = {}   # Layer that will be returned
                bundle["layer"] = layer["layer"]
                bundle["featureType"] = ft["featureType"]
                layers[ws].append(bundle)

        layers = json.dumps(layers) # json -> string
        return (code, layers)

    def deleteLayer(self, workspace, layer): 
        """Delete the Layer and the Corresponding Feature Type
        """
        gsr = GsRest(self.config)
        
        # Find the Feature Type
        headers, response = gsr.getLayer(workspace,layer)
        # TODO: check the result
        layerJson = json.loads(response)
        ftUrl = layerJson["layer"]["resource"]["href"]

        # Delete Layer
        headers, response = gsr.deleteLayer(workspace,layer)
        # TODO: check the result

        # Delete Feature Type
        headers, response = gsr.deleteUrl(ftUrl)
        # TODO: check the result and return st.

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
        #print "*** GET CONFIG***"
        #print headers

        # TODO: check the response
        featureTypeJson = json.loads(response)

        # Return
        retval = {}
        retval["layer"] = layerJson["layer"]
        retval["featureType"] = featureTypeJson["featureType"]
        retval = json.dumps(retval)
        return retval

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

    ### WORKSPACES ###

    def getWorkspaces(self): 
        """json of workspaces, eventually with layers"""
        pass #TODO

    def addWorkspace(self,name,attributes=None): 
        """create workspace"""
        pass #TODO

    def removeWorkspace(self,name): 
        """remove workspace"""
        pass #TODO

    def updateWorkspace(self, name,attributes=None): 
        """updates existing worspace"""
        pass #TODO

