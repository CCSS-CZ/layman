# Lincense: ...
# authors: Michal, Jachym

#TODO: class ServerMan, GeoServ, MapServ and DbMan

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

    def publish(self, fileName, dbName=None, layerName=None, layerParams=None):
        datasourceName = importLayer(fileName,dbName)
        if !datasourceName:
            pass # TODO
        retval = addLayer(datasourceName,layerName,layerParams)
        return retval

    # Import

    def importLayer(self,fileName,dbName=None): 
        """import given file to database, 
        and register layer to geoserver as datasource 
        """
        pass # TODO

    # Layers

    def getLayers(self): 
        """returns list of layers"""
        pass # TODO

    def addLayer(self,datasourceName,layerName=None,layerParams=None):  
        """creates new dataset + configures new layer"""
        pass # TODO

    def deleteLayer(self): 
        """removes layers from database + from mapping server"""
        pass # TODO

    def getLayerParams(self,layer_id): 
        """returns informations about layer"""
        pass # TODO

    def setLayerParams(layer_id,{params}): 
        """sets informations about layer, including service metadata (in cooperation with given catalogue service)"""
        pass # TODO

    # Workspaces

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

