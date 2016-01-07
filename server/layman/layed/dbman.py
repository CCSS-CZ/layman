#
#    LayMan - the Layer Manager
#
#    Copyright (C) 2016 Czech Centre for Science and Society
#    Authors: Jachym Cepicky, Karel Charvat, Stepan Kafka, Michal Sredl, Premysl Vohnout
#    Mailto: sredl@ccss.cz, charvat@ccss.cz
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import subprocess
import psycopg2
import logging
from  layman.errors import LaymanError
from osgeo import ogr
from osgeo import gdal
from StringIO import StringIO
import os
import sys

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
        logStr = "dbname='"+dbname+"' user='"+dbuser+"' host='"+dbhost+"' port='"+dbport+"'" 
        logging.debug("[DbMan][getConnectionString] Connection details: %s"% logStr)

        if ogr:
            retval = "PG: host=%s dbname=%s user=%s password=%s port=%s" %\
                   (dbhost, dbname, dbuser, dbpass, dbport)
        else:
            retval = "dbname='%s' user='%s' host='%s' password='%s'" %\
                   (dbname, dbuser, dbhost, dbpass)

        return retval

    def _convertCpgForPG(self, cpg):
        """ Convert cpgs given in various ways to PG understandable matter, as defined here:
        http://www.postgresql.org/docs/9.2/static/multibyte.html """

        logging.debug("[DbMan][_convertCpgForPG] cpg given: '%s'" % cpg)

        if cpg is None:
            return None

        cpgDic = {}
        cpgDic["UTF-8"] = "UTF8" 
        cpgDic["1250"] = "WIN1250" 
        cpgDic["1251"] = "WIN1251" # 1251 code is used in LayMan Client PublishForm
        cpgDic["WindowsCyrillic"] = "WIN1251" # WindowsCyrillic is used in Mapinfo .TAB file
        cpgDic["1252"] = "WIN1252" 
        cpgDic["1253"] = "WIN1253" 
        cpgDic["1254"] = "WIN1254" 
        cpgDic["1255"] = "WIN1255" 
        cpgDic["1256"] = "WIN1256" 
        cpgDic["1257"] = "WIN1257" 
        cpgDic["1258"] = "WIN1258" 
        cpgDic["1259"] = "WIN1259" 

        pgCpg = cpg
        if cpg in cpgDic:
            pgCpg = cpgDic[cpg]
            logging.debug("[DbMan][_convertCpgForPG] pgCpg identified: %s" % pgCpg)
        else:
            logging.debug("[DbMan][_convertCpgForPG] cpg '%s' not known, pgCpg set to '%s'" % (cpg, pgCpg))

        return pgCpg

    def exportClientEncoding(self, cpg):
        """ Export client encoding to tell PostGIS what it should expect
        This is needed for Mapinfo. 
        For shapefile it is sufficient just to create the .cpg file. """

        if cpg is not None:
            pgCpg = self._convertCpgForPG(cpg)
            if pgCpg is not None:
                os.environ["PGCLIENTENCODING"] = pgCpg
                logging.debug("[DbMan][exportClientEncoding] Env. var. 'PGCLIENTENCODING' set to '%s'" % os.environ["PGCLIENTENCODING"])

        # TODO - cpg comes from the GUI. For Mapinfo, it can be picked up from the .TAB file automatically

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

        # Export client encoding to tell PostGIS what it should expect
        self.exportClientEncoding(cpg)

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
        success = ogr2ogr.main(ogr2ogr_params)
        logging.debug("[DbMan][updateVectorFile] ogr2ogr.main() returned.")

        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        devnull.close()

        if not success:
            logging.error("[DbMan][updateVectorFile] ogr2ogr failed.")
            raise LaymanError(500, "Database import (ogr2ogr) failed. (Is the encoding correct?)")

    def importVectorFile(self, filePath, dbSchema, srs, tsrs, cpg):
        """import given file to database
        If a table of the same name already exists, new name is assigned.
        """
        logParam = "filePath='%s', dbSchema='%s' srs=%s tsrs=%s cpg=%s" % (filePath, dbSchema, str(srs), str(tsrs), str(cpg))
        logging.debug("[DbMan][importVectorFile] %s" % logParam)

        self.createSchemaIfNotExists(dbSchema)
        ds = ogr.Open(filePath)

        layer_in = ds.GetLayerByIndex(0)
        name_out = layer_in.GetName().lower()
        name_out = self._find_new_layername(dbSchema, name_out)

        os.environ["GDAL_DATA"] = self.config.get("Gdal","gdal_data")

        # Export client encoding to tell PostGIS what it should expect
        self.exportClientEncoding(cpg)

        # TODO - Mapinfo - get the proper geometry type

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

        # postgis ignores client_encoding in the connection string.
        # try 'export PGCLIENTENCODING=win1251' instead
        ogr2ogr_params.extend([self.getConnectionString(True), 
                               filePath])
        logging.debug("[DbMan][importVectorFile] Going to call ogr2ogr.main() with the following params: %s" % str(ogr2ogr_params))
        # FIXME: We need to learn the real new name of the table here. 
        # E.g. "some-name" is transferred to "some_name" and we don't have a clue.
        success = ogr2ogr.main(ogr2ogr_params)
        logging.debug("[DbMan][importVectorFile] ogr2ogr.main() returned. Success: %s" % str(success))

        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        devnull.close()

        if not success:
            logging.error("[DbMan][importVectorFile] ogr2ogr failed.")
            raise LaymanError(500, "Database import (ogr2ogr) failed. (Is the encoding correct?)")

        # FIXME: We need to wait until the DB is ready and THEN return. 
        # Otherwise publishing fails and we get 
        # org.postgresql.util.PSQLException: ERROR: LWGEOM_estimated_extent: couldn't locate table within current schema
        # Takes about 12 secs for ArmCommP.shp

        # TODO: Check the result
        # TODO: Exceptions handling
        # TODO: Check if srs and tsrs is valid EPSG code

        logging.debug("[DbMan][importVectorFile] File %s imported as table %s:%s" % (filePath, dbSchema, name_out))

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
        """ tableView = [TABLE|VIEW]
        """
        logParam = "tableName='"+tableName+"', dbSchema='"+dbSchema+"', tableView="+tableView
        logging.debug("[DbMan][deleteTable] %s"% logParam)

        try: 
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

    ### LAYPAD ###

    def createLayerPad(self, name, title, group, owner, layertype, datagroup, dataname):
        """ Create Layer in LayPad 
        """
        logParam =  "name: " + name + "title: " +title+ " group: " + group + " owner: " + owner + "type: " + layertype + " datagroup: " + datagroup + " dataname: " + dataname
        logging.debug("[DbMan][createLayerPad] %s" % logParam)

        sqlBatch = "insert into layman.layers (layername, layergroup, layertitle, owner, type, datagroup, dataname) values ('"+name+"','"+group+"','"+title+"','"+owner+"','"+layertype+"','"+datagroup+"','"+dataname+"');"
        self.write_sql(sqlBatch)

    def updateLayerPad():        
        pass

    def deleteLayerPad(self, name, group):
        """ Delete layer in LayPad
        """
        logParam =  "name: " + name + " group: " + group
        logging.debug("[DbMan][deleteLayerPad] %s" % logParam)

        sqlBatch = "delete from layman.layers where layername='"+name+"' and layergroup='"+group+"';"
        self.write_sql(sqlBatch)

    def getLayerPad(self, owner=None):
        """ Get Layers from layman.layers
            owner given - just for this user
            owner not given - all the layers
            Returns JSON:
            [
               {
                    layername: 
                    layergroup:
                    layertitle:
                    owner:
                    type:
                    datagroup:
                    dataname:
               },
                ...

            ]
        """
        logging.debug("[DbMan][getLayerPad] owner='%s'"% owner)

        if owner is None:
            sql = "SELECT layername, layergroup, layertitle, owner, type, datagroup, dataname FROM layman.layers;"
        else:
            sql = "SELECT layername, layergroup, layertitle, owner, type, datagroup, dataname FROM layman.layers where owner='"+owner+"';"

        result = self.get_sql(sql) # [['rivers','hasici','Reky','hsrs','vector','hasici','rivers_01'], ... ]
        layers = map( lambda rec: {"layername": rec[0], "layergroup": rec[1], "layertitle": rec[2], "owner": rec[3], "type": rec[4], "datagroup": rec[5], "dataname": rec[6]}, result )

        return layers        

    ### DATAPAD ###

    def createDataPad(self, name, group, owner, dtype, datatype):
        """ Create Data in DataPad 
            dtype - table, view, file
            datatype - vector, raster
        """
        logParam =  "name: " + name + " group: " + group + " owner: " + str(owner) + "dtype: " + dtype + "datatype: " + datatype 
        logging.debug("[DbMan][createDataPad] %s" % logParam)

        sqlBatch = "insert into layman.data (dataname, datagroup, owner, type, datatype) values ('"+name+"','"+group+"',"+ self._stringOrNull(owner) +",'"+dtype+"','"+datatype+"');"
        self.write_sql(sqlBatch)

    def _stringOrNull(self, value=None):
        if value is None:
            return "NULL"
        else:
            return "'"+ value +"'"

    def deleteDataPad(self, group, dtype, name):
        """ Delete data in DataPad
        """
        logParam =  "name: " + name + " group: " + group + "type:" + dtype
        logging.debug("[DbMan][deleteDataPad] %s" % logParam)

        sqlBatch = "delete from layman.data where dataname='"+name+"' and datagroup='"+group+"' and type='"+dtype+"';"
        self.write_sql(sqlBatch)

    def updateDataPad():
        pass

    def getDataPad(self, restrictBy=None, groups=None, owner=None):
        """ Get Data from layman.data

            restrictBy = ['owner'|'roles'|None]
                'owner' - just this owner (user) // owner must be given
                'groups' - just this roles (schemas) // list of roles must be given
                None    - all
          
            Returns JSON:
            [
               {
                    name:
                    schema:
                    owner:
                    type:
                    datatype:
               },
                ...
            ]
        """
        logParam =  "restrictBy: " + str(restrictBy) + " groups: " + str(groups) + "owner: " + str(owner)
        logging.debug("[DbMan][getDataPad] %s" % logParam)

        if restrictBy is None:
            sql = "SELECT dataname, datagroup, owner, type, datatype FROM layman.data;"

        elif restrictBy.lower() in ["owner","user"]:
            if owner is None:
                logging.error("[DbMan][getDataPad] getDataPad() called with restrictBy owner, but no owner given")
                raise LaymanError(500, "Cannot get Data, no owner was specified for getDataPad()")
            sql = "SELECT dataname, datagroup, owner, type, datatype FROM layman.data where owner='"+owner+"';"

        elif restrictBy.lower() in ["roles", "groups", "schemas"]:
            if groups is None:
                logging.error("[DbMan][getDataPad] getDataPad() called with restrictBy roles, but no roles given")
                raise LaymanError(500, "Cannot get Data, no roles were specified for getDataPad()")        
            groups = ",".join(map( lambda g: "'"+g+"'", groups )) # "'aaa','bbb','ccc'"
            sql = "SELECT dataname, datagroup, owner, type, datatype FROM layman.data where datagroup IN (" + groups +")"

        result = self.get_sql(sql) # [['rivers_00','hasici','hsrs','table','vector'], ... ]
        data = map( lambda rec: {"name": rec[0], "schema": rec[1], "owner": rec[2], "type": rec[3], "datatype": rec[4]}, result )

        return data        

    ### CKANPAD ###

    def getCkanResourcesCount(self, ckanUrl, resFormat):
        """ Get number of resources of given format equipped with the age of the information
        """
        logParam =  "ckanUrl: " + ckanUrl + " resFormat: " + resFormat  
        logging.debug("[DbMan][getCkanResourcesCount] %s" % logParam)

        sql = "select (count, now()-ts) from layman.ckanres where ckan='"+ckanUrl+"' and format='"+resFormat+"';"

        result = self.get_sql(sql) # [5, 00:18:13.123456]

        return result

    def createCkanResourcesCount(self, ckanUrl, resFormat, count):
        """ Insert count of resources of given type in ckan specified
        """
        logParam =  "ckanUrl: " + ckanUrl + " resFormat: " + resFormat + " count: " + str(count) 
        logging.debug("[DbMan][createCkanResourcesCount] %s" % logParam)

        sqlBatch = "insert into layman.ckanres (ckan, format, count, ts) values ('"+ckanUrl+"','"+resFormat+"',"+ count +", (select now()) );"
        self.write_sql(sqlBatch)

        return 

    def updateCkanResourcesCount(self, ckanUrl, resFormat, count):
        """ Update count of resources of given type in ckan specified
        """
        logParam =  "ckanUrl: " + ckanUrl + " resFormat: " + resFormat + " count: " + str(count) 
        logging.debug("[DbMan][updateCkanResourcesCount] %s" % logParam)

        sqlBatch = "update layman.ckanres set count="+count+", ts=(select now()) where ckan='"+ckanUrl+"' and format='"+resFormat+"';"
        self.write_sql(sqlBatch)

        return 

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

