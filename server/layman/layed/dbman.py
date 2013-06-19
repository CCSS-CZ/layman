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

from layman import raster2pgsql

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

    def getConnectionString(self,ogr=False):
        dbname = self.config.get("DbMan","dbname")
        dbuser = self.config.get("DbMan","dbuser")
        dbhost = self.config.get("DbMan","dbhost")
        dbpass = self.config.get("DbMan","dbpass")
        dbport = self.config.get("DbMan","dbport")
        logStr = "dbname='"+dbname+"' user='"+dbuser+"' host='"+dbhost+"'"
        logging.debug("[DbMan][getConnectionString] Connection details: %s"% logStr)

        if ogr:
            return "PG: host=%s dbname=%s user=%s password=%s port=%s"%\
                    (dbhost, dbname,dbuser,dbpass,dbport)
        else:
            return "dbname='"+dbname+"' user='"+dbuser+"' host='"+dbhost+"' password='"+dbpass+"'"

    # Import

    def importFile(self, filePath, dbSchema, data_type="vector"):
        if data_type == "vector":
            self.importVectorFile(filePath, dbSchema)
        else:
            self.importRasterFile(filePath, dbSchema)

    def importVectorFile(self, filePath, dbSchema): 
        """import given file to database, ogr is used for data READING, psycopg2
        for data WRITING directly into PostGIS
        """
        logParam = "filePath='"+filePath+"', dbSchema='"+dbSchema+"'"
        logging.debug("[DbMan][importVectorFile] %s"% logParam)

        self.createSchemaIfNotExists(dbSchema)
        ds = ogr.Open(filePath)

        sqlBatch = None

        for i in range(ds.GetLayerCount()):
            layer_in = ds.GetLayerByIndex(i)

            if layer_in:

                name_out = layer_in.GetName().lower()
                name_out = self._find_new_layername(dbSchema,name_out)
                # TODO: data exists, throw exception
                #if pg_out.GetLayerByName(name_out):
                #    pass

                logging.debug("[DbMan][importVectorFile] Going to assemble the SQL...")
                sqlBatch = self._get_vector_file_import_sql(ds, dbSchema,name_out)
                logging.debug("[DbMan][importVectorFile] SQL assembled: %s"% sqlBatch)

                if sqlBatch:
                    logging.debug("[DbMan][importVectorFile] Going to write the SQL...")
                    self.write_sql(sqlBatch)
                    logging.debug("[DbMan][importVectorFile] SQL written")
        
        return name_out
        #TODO return table name

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

    def write_sql(self,sqlBatch):
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
            logging.debug("[DbMan][importFile] %s"% errStr)
            raise LaymanError(500, "DbMan: "+errStr)

    def _get_vector_file_import_sql(self, file_in, dbSchema, name_out):
        """Import vector file
        """
        logParam = "dbSchema='"+dbSchema+"', name_out='"+name_out+"'"
        logging.debug("[DbMan][_get_vector_file_import_sql] %s"% logParam)

        sqlBatch = ""

        # for each layer within the file
        # NOTE: in Shapefile, there is usually only one layer
        layer_count = 0
        for layer_in in file_in:
            layer_count_str = str(layer_count)
            logging.debug("[DbMan][_get_vector_file_import_sql] layer %s"% layer_count_str)
            layer_count += 1

            # begin table creation
            sqlBatch += "SET search_path TO "+dbSchema+",public;\n"
            sqlBatch += "SET CLIENT_ENCODING TO UTF8;\n"
            sqlBatch += "SET STANDARD_CONFORMING_STRINGS TO ON;\n"
            sqlBatch += 'CREATE TABLE '+dbSchema+"."+name_out+' (\n';
            sqlBatch +="gid serial,\n"

            # layer columns definition
            dfn = layer_in.GetLayerDefn()
            fieldCount = dfn.GetFieldCount()
            fields = []

            j = 0
            # create columns
            while j < fieldCount:
                fieldDfn = dfn.GetFieldDefn(j)
                fieldName = fieldDfn.GetName()
                field_type = self._getSqlTypeFromType(fieldDfn.GetType())
                fieldName_str = str(fieldName)
                logging.debug("[DbMan][_get_vector_file_import_sql] field: '%s'"% fieldName_str)
                comma = ",\n"
                if j+1 == fieldCount:
                    comma = ""
                sqlBatch += '"'+fieldName.lower()+'" '+ field_type + comma
                fields.append((fieldName,field_type))
                j += 1
            sqlBatch += ");\n"
            sqlBatch += 'ALTER TABLE '+dbSchema+"."+name_out+' ADD PRIMARY KEY (gid);\n'

            # add geometry column
            (geom_type, dimensions) = self._getGeomType(layer_in.GetGeomType())
            sqlBatch += "".join(["SELECT AddGeometryColumn('",
                                  dbSchema,
                                  "','",
                                  name_out,
                                 "','geom','0','",
                                 geom_type,
                                 "',"+str(dimensions)+");\n"])
            fields.append(("geom","geometry"))

            # database prepared, feed it
            logging.debug("[DbMan][_get_vector_file_import_sql] Database prepared, going to feed it...")
            feature = layer_in.GetNextFeature()
            strfields = map(lambda field: '"%s"' % field[0], fields)

            # insert each feature into database table
            feature_count = 0
            while feature:
                vals = map(lambda field: "%s" % \
                                self._adjust_value(feature.GetField(field[0]),field[1]),
                            fields[:-1]
                        )
                feature_count_str = str(feature_count)
                logging.debug("[DbMan][_get_vector_file_import_sql] feature %s"% feature_count_str)
                feature_count += 1

                geom = feature.GetGeometryRef().ExportToWkt()

                # we have to convert polygons to multipolygons
                if geom.find("POLYGON") == 0:
                    geom = geom.replace("POLYGON","MULTIPOLYGON(")
                    geom = geom+")"

                # add geometry to values
                vals.append("ST_AsText('"+geom+"')")

                sqlBatch += 'INSERT INTO %(schema)s.%(table)s (%(columns)s) VALUES (%(values)s);' %\
                        ({
                            "schema":dbSchema,
                            "table": name_out,
                            "columns": ",".join(strfields).lower(),
                            "values": ",".join(vals)
                        })
                        
                feature = layer_in.GetNextFeature()

            return sqlBatch

    def _clean_string_vals(self, val):
        """Clean string to be sql usable
        """

        if type(val) == type(''):
            val = val.replace("'","%s'"%"\'")
        return val

    def _get_raster_file_import_sql(self, filePath,dbSchema,table):
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
            params = (dbSchema, )
            cur.execute(SQL, params) 
            result = cur.fetchone()

            created = False
            if not result:
                SQL = "CREATE SCHEMA "+dbSchema+";"
                cur.execute(SQL) 
                created = True            

            conn.commit()
            cur.close()
            conn.close()
            if created:
                logging.info("[DbMan][createSchemaIfNotExists] Created schema %s"% dbSchema)

        except Exception as e:
            errStr = "Database (psycopg2) error: '"+str(e)+"'"
            logging.debug("[DbMan][createSchemaIfNotExists] %s"% errStr)
            raise LaymanError(500, "DbMan: "+errStr)

    # Delete 
    def deleteTable(self, dbSchema, tableName): 
        logParam = "tableName='"+tableName+"', dbSchema='"+dbSchema+"'"
        logging.debug("[DbMan][deleteTable] %s"% logParam)
 
        try: # TODO: extract to one function
            # connect
            conn = psycopg2.connect(self.getConnectionString())
 
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

    def _getSqlTypeFromType(self,tp):
        """Return string representing propper data type, based on given input
        data type (usually from shapefile)
        """

        if tp == ogr.OFTReal:
            return "real"
        elif tp == ogr.OFTInteger:
            return "integer"
        elif tp == ogr.OFTString:
            return "varchar(256)"
        elif tp == ogr.OFTWideString:
            return "text"
        else:
            return "varchar(256)"

        # FIXME add more

    def _adjust_value(self,value, ftype):
        """Return string representig value, acceptable by sql
        """

        if value == None:
            return "NULL"
        elif ftype == "real":
            return str(float(value))
        elif ftype == "integer":
            return str(int(value))
        else:
            value = value.replace("'","%s'"%"\'")
            return "'%s'" % value

        # FIXME add more

    def _getGeomType(self,geomtype):
        """Return string representing propper geometry type, based on given input
        data ogr
        """

        if geomtype == ogr.wkbPolygon:
            return ("MULTIPOLYGON",2)
        elif geomtype == ogr.wkbMultiPolygon:
            return ("MULTIPOLYGON",2)
        elif geomtype == ogr.wkbPolygon25D:
            return ("MULTIPOLYGON",3)
        elif geomtype == ogr.wkbPoint:
            return ("POINT",2)
        elif geomtype == ogr.wkbLineString:
            return ("LINESTRING",2)
        # FIXME: add more

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
