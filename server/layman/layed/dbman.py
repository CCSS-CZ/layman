# Lincense: ...
# authors: Michal, Jachym

import subprocess
import psycopg2
import logging
from  layman.errors import LaymanError
from osgeo import ogr
from osgeo import gdal
from StringIO import StringIO
import os
import sys
from osgeo import gdal

import time

from layman import raster2pgsql
from layman import ogr2ogr

#FIXME: Prevent SQL injection

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

    def getConnectionString(self, ogr=False):
        dbname = self.config.get("DbMan","dbname")
        dbuser = self.config.get("DbMan","dbuser")
        dbhost = self.config.get("DbMan","dbhost")
        dbpass = self.config.get("DbMan","dbpass")
        dbport = self.config.get("DbMan","dbport")
        logStr = "dbname='"+dbname+"' user='"+dbuser+"' host='"+dbhost+"' pass='"+dbpass+"' port='"+dbport+"'" # FIXME: remove password
        logging.debug("[DbMan][getConnectionString] Connection details: %s"% logStr)

        if ogr:
            return "PG: host=%s dbname=%s user=%s password=%s port=%s" %\
                   (dbhost, dbname, dbuser, dbpass, dbport)
        else:
            return "dbname='%s' user='%s' host='%s' password='%s'" %\
                   (dbname, dbuser, dbhost, dbpass)

    # Import
    def importFile(self, filePath, dbSchema, data_type="vector"):
        if data_type == "vector":
            self.importVectorFile(filePath, dbSchema)
        else:
            self.importRasterFile(filePath, dbSchema)

    def updateVectorFile(self, filePath, dbSchema, table_name):
        """Update existing postgresql table with given file
        """
        logParam = "filePath='%s', dbSchema='%s'" % (filePath, dbSchema)
        logging.debug("[DbMan][updateVectorFile] %s" % logParam)

        os.environ["GDAL_DATA"] = self.config.get("Gdal","gdal_data")
        devnull = open(os.devnull, "w")
        sys.stdout = sys.__stderr__
        sys.stderr = devnull
        ogr2ogr_params = ["", "-lco", "OVERWRITE=YES",
                          "-lco", "SCHEMA=" + str(dbSchema),
                          "-lco", "PRECISION=NO",
                          "-nln", table_name, "-f", "PostgreSQL"]

        if self._get_ogr2ogr_version() >= 1100000:
            ogr2ogr_params.extend(["-nlt", "PROMOTE_TO_MULTI"])

        ogr2ogr_params.extend([self.getConnectionString(True),
                               filePath])

        logging.debug("[DbMan][updateVectorFile] Going to call ogr2ogr.main() with the following params: %s" % str(ogr2ogr_params))
        ogr2ogr.main(ogr2ogr_params)
        logging.debug("[DbMan][updateVectorFile] ogr2ogr.main() returned.")

        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        devnull.close()

    def importVectorFile(self, filePath, dbSchema, srs, tsrs):
        """import given file to database, ogr is used for data READING,
        psycopg2 for data WRITING directly into PostGIS
        If a table of the same name already exists, new name is assigned.
        """
        logParam = "filePath='%s', dbSchema='%s'" % (filePath, dbSchema)
        logging.debug("[DbMan][importVectorFile] %s" % logParam)

        self.createSchemaIfNotExists(dbSchema)
        ds = ogr.Open(filePath)

        layer_in = ds.GetLayerByIndex(0)
        name_out = layer_in.GetName().lower()
        name_out = self._find_new_layername(dbSchema, name_out)

        os.environ["GDAL_DATA"] = self.config.get("Gdal","gdal_data")

        logging.debug("[DbMan][importVectorFile] Going to import layer to db...")
        # hack -> everthing to devnull
        devnull = open(os.devnull, "w")
        sys.stdout = sys.__stderr__
        sys.stderr = devnull
        ogr2ogr_params = ["", "-lco", "SCHEMA=" + str(dbSchema),
                          "-lco", "PRECISION=NO",
                          "-nln", name_out, "-f", "PostgreSQL", "-s_srs", srs, "-t_srs", tsrs]

        if self._get_ogr2ogr_version() >= 1100000:
            ogr2ogr_params.extend(["-nlt", "PROMOTE_TO_MULTI"])

        ogr2ogr_params.extend([self.getConnectionString(True),
                               filePath])
        logging.debug("[DbMan][importVectorFile] Going to call ogr2ogr.main() with the following params: %s" % str(ogr2ogr_params))
        ogr2ogr.main(ogr2ogr_params)
        logging.debug("[DbMan][importVectorFile] ogr2ogr.main() returned.")

        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        devnull.close()

        # FIXME: We need to wait until the DB is ready and THEN return. 
        # Otherwise publishing fails and we get 
        # org.postgresql.util.PSQLException: ERROR: LWGEOM_estimated_extent: couldn't locate table within current schema
        # Takes about 12 secs for ArmCommP.shp

        # TODO: Check the result
        # TODO: Exceptions handling
        # TODO: Check if srs and tsrs is valid EPSG code

        return name_out

    def _find_new_layername(self, schema, name):
        """
        Finds new layer name, which does not exist in the database yet
        """

        conn = psycopg2.connect(self.getConnectionString())
        cur = conn.cursor()

        cur.execute("SELECT relname  FROM pg_stat_user_tables WHERE schemaname = '%s' AND relname like '%s_%%' " % (schema,name))
        tables = map(lambda t: t[0], cur.fetchall())
        if len(tables) > 0:
            tables.sort()
            splitn = tables[-1].split("_")
            name = "_".join(splitn[:-1])
            try:
                nr = int(splitn[-1])
                name = "%s_%02d" % (name, int(nr+1))
            except:
                name = "%s_%s_00" % (name, splitn[-1])
        else:
            return "%s_00"%name

        return name

    def importRasterFile(self, filePath, dbSchema):
        """Import raster file into POSTGIS database
        """
        name_out = os.path.splitext(os.path.split(filePath)[1])[0]
        sqlBatch = self._get_raster_file_import_sql(filePath,dbSchema,name_out)

        if sqlBatch:
            logParam = "filePath='"+filePath+"', dbSchema='"+dbSchema+"'"
            logging.debug("[DbMan][importRasterFile] %s"% logParam)

            self.write_sql(sqlBatch)

    def write_sql(self, sqlBatch):
        try:
            conn = psycopg2.connect(self.getConnectionString())
            cur = conn.cursor()

            cur.execute(sqlBatch)
            conn.commit()

            #close
            cur.close()
            conn.close()
        except Exception as e:
            errStr = "Database (psycopg2) error: '"+str(e)+"'"
            logging.debug("[DbMan][write_sql] %s"% errStr)
            raise LaymanError(500, "DbMan: "+errStr)

    def _get_raster_file_import_sql(self, filePath, dbSchema, table):
        """Import raster file
        """
        import sys
        sys.stdout = sys.stderr
        global RASTER2PSQL_CONFIG
        RASTER2PSQL_CONFIG["filename"] = filePath
        RASTER2PSQL_CONFIG["output"] = StringIO()
        RASTER2PSQL_CONFIG["table"] = table

        raster2pgsql.g_rt_schema = dbSchema


        raster2pgsql.parse_command_line = parse_raster2psql_command_line
        raster2pgsql.main()

        sys.stdout = sys.__stdout__

        sqlBatch = """BEGIN;
        CREATE TABLE %s.%s ("rid" serial PRIMARY KEY,"rast" raster);
        """ % (dbSchema, table)
        sqlBatch += RASTER2PSQL_CONFIG["output"].getvalue()
        sqlBatch += "END;"

        return sqlBatch

    def createSchemaIfNotExists(self, dbSchema):
        logParam = "dbSchema='"+dbSchema+"'"
        logging.debug("[DbMan][createSchemaIfNotExists] %s"% logParam)

        try:
            dbSchema = dbSchema.lower()

            conn = psycopg2.connect(self.getConnectionString())
            cur = conn.cursor()

            SQL = "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s;"
            # SQL = "SELECT schema_name FROM information_schema.schemata;"
            params = (dbSchema, )
            logging.debug("[DbMan][createSchemaIfNotExists] Checking schema '%s'..."% dbSchema)
            logging.debug("[DbMan][createSchemaIfNotExists] SQL: '%s', Params: '%s'..."% (SQL, params))
            cur.execute(SQL, params)
            #cur.execute(SQL)
            result = cur.fetchall()
            logging.debug("[DbMan][createSchemaIfNotExists] Select result: '%s'"% str(result))

            created = False
            if not result:
                logging.debug("[DbMan][createSchemaIfNotExists] Schema not found, create schema")
                SQL = "CREATE SCHEMA "+dbSchema+";"
                cur.execute(SQL)
                created = True
            else:
                logging.debug("[DbMan][createSchemaIfNotExists] Schema found, go on")

            conn.commit()
            cur.close()
            conn.close()
            if created:
                logging.info("[DbMan][createSchemaIfNotExists] Created schema %s"% dbSchema)

        except Exception as e:
            errStr = "Database (psycopg2) error: '"+str(e)+"'"
            logging.debug("[DbMan][createSchemaIfNotExists] %s"% errStr)
            raise LaymanError(500, "DbMan: "+errStr)

    # Get the list of tables from the schemas from the given list
    def getTables(self, schemalist):

        schemata = ",".join(map( lambda s: "'"+s+"'", schemalist )) # "'aaa','bbb','ccc'"
        sql = "SELECT schemaname, relname FROM pg_stat_user_tables WHERE schemaname IN (" + schemata + ")" 

        result = self.get_sql(sql) # [['hasici','pest'], ['policajti','azov'] ...]
        tables = map( lambda rec: {"schema": rec[0], "name": rec[1]}, result )

        return tables        

    # Get the list of views from the schemas from the given list
    def getViews(self, schemalist):

        schemata = ",".join(map( lambda s: "'"+s+"'", schemalist )) # "'aaa','bbb','ccc'"
        sql = "SELECT schemaname, viewname FROM pg_views WHERE schemaname IN (" + schemata + ")" 

        result = self.get_sql(sql) # [['hasici','pest'], ['policajti','azov'] ...]
        views = map( lambda rec: {"schema": rec[0], "name": rec[1]}, result )

        return views               
 
    def get_sql(self, sqlBatch):
        try:
            conn = psycopg2.connect(self.getConnectionString())
            cur = conn.cursor()

            cur.execute(sqlBatch)
            retval = cur.fetchall()

            conn.commit()
            cur.close()
            conn.close()

            return retval

        except Exception as e:
            errStr = "Database (psycopg2) error: '" + str(e) + "'"
            logging.debug("[DbMan][get_sql] %s"% errStr)
            raise LaymanError(500, "DbMan: " + errStr)

    # Delete
    def deleteTable(self, dbSchema, tableName, tableView = "TABLE"):
        logParam = "tableName='"+tableName+"', dbSchema='"+dbSchema+"', tableView="+tableView
        logging.debug("[DbMan][deleteTable] %s"% logParam)

        try: # TODO: extract to one function
            # connect
            conn = psycopg2.connect(self.getConnectionString())

            # set schema
            setSchemaSql = "SET search_path TO "+dbSchema+",public;"

            # delete table
            deleteTableSql = "DROP " + tableView + " \""+tableName+"\";"

            # execute
            cur = conn.cursor()
            logging.debug("[DbMan][deleteTable] set schema: '%s'"% setSchemaSql)
            cur.execute(setSchemaSql) 
            logging.debug("[DbMan][deleteTable] deleteTableSql: %s"% deleteTableSql)
            cur.execute(deleteTableSql) 
            conn.commit()

            #close
            cur.close()
            conn.close()
        except Exception as e:
            errStr = "Database (psycopg2) error: '"+str(e)+"'"
            logging.debug("[DbMan][deleteTable] %s"% errStr)
            raise LaymanError(500, "DbMan: "+errStr)

    def deleteView(self, dbSchema, viewName): 
        logParam = "viewName='"+viewName+"', dbSchema='"+dbSchema+"'"
        logging.debug("[DbMan][deleteView] %s"% logParam)
        self.deleteTable(dbSchema, viewName, "VIEW")

    def _get_ogr2ogr_version(self):
        """Returns version of OGR2OGR as (major,minor,release) triplet
        """

        return int(gdal.VersionInfo())

RASTER2PSQL_CONFIG = {}

def parse_raster2psql_command_line():
    """should return back propper configuration for raster2pgsql.main
    """

    global RASTER2PSQL_CONFIG

    class Opts(object):
        pass
    opts = Opts()
    args = Opts()

    opts.verbose = True
    opts.output = RASTER2PSQL_CONFIG["output"]

    opts.raster = [RASTER2PSQL_CONFIG["filename"]]
    opts.table =  RASTER2PSQL_CONFIG["table"]

    # default configuration
    opts.endian = raster2pgsql.g_rt_endian
    opts.version = raster2pgsql.g_rt_version
    opts.srid = -1
    opts.band = None
    opts.block_size = None
    opts.register = False
    opts.overview_level = 1

    opts.create_table = False
    opts.append_table = False
    opts.drop_table = False
    opts.column = "rast" #raster2pgsql.g_rt_column
    opts.filename = False
    opts.index = False
    opts.vacuum = False
    opts.create_raster_overviews_table = False

    return  (opts, args)

