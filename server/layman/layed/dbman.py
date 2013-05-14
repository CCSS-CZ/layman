# Lincense: ...
# authors: Michal, Jachym

import subprocess
import psycopg2
import logging
from  layman.errors import LaymanError

class DbMan:
    """PostGis db interface
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

    # Import

    def importShapeFile(self, filePath, dbSchema): 
        """import given file to database, 
        """
        # shp2pgsql #
        logParam = "filePath='"+filePath+"', dbSchema='"+dbSchema+"'"
        logging.debug("[DbMan][importShapeFile] %s"% logParam)
        try: 
            # viz tez:http://www.moosechips.com/2010/07/python-subprocess-module-examples/
            sqlBatch = subprocess.check_output(['shp2pgsql',filePath])
        except subprocess.CalledProcessError as e:
            errStr = "shp2pgsql error: '"+str(e)+"'"
            logging.debug("[DbMan][importShapeFile] %s"% errStr)
            raise LaymanError(500, "DbMan: "+errStr)
 
        # import - run the batch through psycopg2 #

        # TODO: create the schema if it does not exist

        dbname = self.config.get("DbMan","dbname")
        dbuser = self.config.get("DbMan","dbuser")
        dbhost = self.config.get("DbMan","dbhost")
        dbpass = self.config.get("DbMan","dbpass")
        connectionString = "dbname='"+dbname+"' user='"+dbuser+"' host='"+dbhost+"' password='"+dbpass+"'"
        logStr = "dbname='"+dbname+"' user='"+dbuser+"' host='"+dbhost+"'"
        logging.debug("[DbMan][importShapeFile] Connection details: %s"% logStr)


        try:
            # connect
            conn = psycopg2.connect(connectionString)
 
            # set schema
            setSchemaSql = "SET search_path TO "+dbSchema+",public;"

            # execute
            cur = conn.cursor()
            logging.debug("[DbMan][importShapeFile] set schema: '%s'"% setSchemaSql)
            cur.execute(setSchemaSql) # TODO check the success
            logging.debug("[DbMan][importShapeFile] sqlBatch: %s"% sqlBatch)
            cur.execute(sqlBatch) # TODO check the success
            conn.commit()
        
            #close
            cur.close()
            conn.close()
        except Exception as e:
            errStr = "Database (psycopg2) error: '"+str(e)+"'"
            logging.debug("[DbMan][importShapeFile] %s"% errStr)
            raise LaymanError(500, "DbMan: "+errStr)
        
        #TODO return table name

