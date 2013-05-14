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
    connectionString = ""

    def __init__(self,config = None):
        """constructor
        """

        ## get configuration parser
        self._setConfig(config)
        self._setConnectionString()

    def _setConfig(self,config):
        """Get and set configuration files parser
        """
        if config:
            self.config = config
        else:
            from layman import config
            self.config =  config

    def _setConnectionString(self):
        dbname = self.config.get("DbMan","dbname")
        dbuser = self.config.get("DbMan","dbuser")
        dbhost = self.config.get("DbMan","dbhost")
        dbpass = self.config.get("DbMan","dbpass")
        self.connectionString = "dbname='"+dbname+"' user='"+dbuser+"' host='"+dbhost+"' password='"+dbpass+"'"
        logStr = "dbname='"+dbname+"' user='"+dbuser+"' host='"+dbhost+"'"
        logging.debug("[DbMan][_setConnectionString] Connection details: %s"% logStr)

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

        try:
            # connect
            conn = psycopg2.connect(self.connectionString)
 
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

    # Delete 

    def deleteTable(self, dbSchema, tableName): 
        logParam = "tableName='"+tableName+"', dbSchema='"+dbSchema+"'"
        logging.debug("[DbMan][deleteTable] %s"% logParam)
 
        try: # TODO: extract to one function
            # connect
            conn = psycopg2.connect(self.connectionString)
 
            # set schema
            setSchemaSql = "SET search_path TO "+dbSchema+",public;"

            # delete table
            deleteTableSql = "DROP TABLE \""+tableName+"\";"

            # execute
            cur = conn.cursor()
            logging.debug("[DbMan][deleteTable] set schema: '%s'"% setSchemaSql)
            cur.execute(setSchemaSql) # TODO check the success
            logging.debug("[DbMan][deleteTable] deleteTableSql: %s"% deleteTableSql)
            cur.execute(deleteTableSql) # TODO check the success
            conn.commit()
        
            #close
            cur.close()
            conn.close()
        except Exception as e:
            errStr = "Database (psycopg2) error: '"+str(e)+"'"
            logging.debug("[DbMan][deleteTable] %s"% errStr)
            raise LaymanError(500, "DbMan: "+errStr)
        
        #TODO return table name
