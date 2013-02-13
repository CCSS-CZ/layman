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

    def publish(self, filePath, dbSchema, gsWorkspace, layerName):
        """ Main publishing function. 
            Group ~ db Schema ~ gs Data Store ~ gs Workspace
        """
        tableName = importShapeFile(filePath) # TODO check the result

        # TODO - check the GS workspace and create it if it does not exist 
        # if...
        #    createWorkspace(...)

        # Here the Workspace should exist

        # TODO - check the GS data store and create it if it does not exist 
        # if...
        #    createDataStore(...)

        # Here the Data Store should exist

        retval = addLayer(datasourceName,layerName,layerParams)
        return retval

    # Import

    def importShapeFile(self,filePath): 
        """import given file to database, 
        """
        # shp2pgsql #

        import subprocess
        try: 
            # viz tez:http://www.moosechips.com/2010/07/python-subprocess-module-examples/
            sqlBatch = subprocess.check_output(['shp2pgsql',filePath])
        except subprocess.CalledProcessError as e:
            print "shp2pgsql error:"
            print e
            pass # TODO
 
        # import - run the batch through psycopg2 #

        #TODO: USE PROPER DATABASE SCHEMA!!!

        import psycopg2

        dbname = self.config.get("LayEd","dbname")
        dbuser = self.config.get("LayEd","dbuser")
        dbhost = self.config.get("LayEd","dbhost")
        dbpass = self.config.get("LayEd","dbpass")
        connectionString = "dbname='"+dbname+"' user='"+dbuser+"' host='"+dbhost+"' password='"+dbpass+"'"

        try:
            # connect
            conn = psycopg2.connect(connectionString)
 
            # execute
            cur = conn.cursor()
            cur.execute(sqlBatch) # TODO check the success
            conn.commit()
        
            #close
            cur.close()
            conn.close()
        except Exception as e:
            print "Database error: " #TODO
            print e
        
        #TODO return table name

    def createDataStore(self):
        pass # TODO

    # Layers

    def getLayers(self, workspace=None): 
        """returns list of layers"""
        from layman.geoserver import GeoServer
        gs = GeoServer()

        code = 200
        layers =  gs.getLayers() # TODO: select only those from the given workspace
        # NOTE: Do we want to get layers or feature types? (two different things in gs)

        return (code,layers)

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

