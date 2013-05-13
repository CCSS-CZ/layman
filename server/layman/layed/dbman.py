# Lincense: ...
# authors: Michal, Jachym

import subprocess
import psycopg2

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

        try: 
            # viz tez:http://www.moosechips.com/2010/07/python-subprocess-module-examples/
            sqlBatch = subprocess.check_output(['shp2pgsql',filePath])
            print sqlBatch
        except subprocess.CalledProcessError as e:
            print "shp2pgsql error:"
            print e
            pass # TODO
 
        # import - run the batch through psycopg2 #

        dbname = self.config.get("DbMan","dbname")
        dbuser = self.config.get("DbMan","dbuser")
        dbhost = self.config.get("DbMan","dbhost")
        dbpass = self.config.get("DbMan","dbpass")
        connectionString = "dbname='"+dbname+"' user='"+dbuser+"' host='"+dbhost+"' password='"+dbpass+"'"

        try:
            # connect
            conn = psycopg2.connect(connectionString)
 
            # set schema
            setSchemaSql = "SET search_path TO "+dbSchema+",public;"

            # execute
            cur = conn.cursor()
            cur.execute(setSchemaSql) # TODO check the success
            cur.execute(sqlBatch) # TODO check the success
            conn.commit()
        
            #close
            cur.close()
            conn.close()
        except Exception as e:
            print "Database error: " #TODO
            print e
        
        #TODO return table name

