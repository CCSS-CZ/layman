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

    def publish(self, filePath, layerName=None, layerParams=None):
        tableName = importLayer(filePath) # TODO check the result
        createDatasource(tableName) # TODO check the result
        retval = addLayer(datasourceName,layerName,layerParams)
        return retval

    # Import

    def importLayer(self,filePath): 
        """import given file to database, 
        and register layer to geoserver as datasource 
        """
        # shp2pgsql #

        import subprocess
        sqlBatch = subprocess.check_output(['shp2pgsql',filePath]) # TODO: check the errorrs

        # import - run the batch through psycopg2 #

        import psycopg2

        # connect
        dbname = config.get("LayEd","dbname")
        dbuser = config.get("LayEd","dbuser")
        dbhost = config.get("LayEd","dbhost")
        dbpass = config.get("LayEd","dbpass")
        try:
            conn = psycopg2.connect("dbname='"+dbname+"' user='"+dbuser+"' host='"+dbhost+"' password='"+dbpass)
        except:
            print "I am unable to connect to the database"#TODO
        
        # execute
        cur = conn.cursor()
        cur.execute(sqlBatch) # TODO check the success
        conn.commit()
        
        #close
        cur.close()
        conn.close()
        
        #TODO return table name

    def createDatasource(self,tableName):
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

    def setLayerParams(layer_id,params=None): 
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

