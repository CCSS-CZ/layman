# Lincense: ...
# authors: Michal, Jachym

import subprocess
import psycopg2
import logging
from  layman.errors import LaymanError
from osgeo import ogr

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
        logStr = "dbname='"+dbname+"' user='"+dbuser+"' host='"+dbhost+"'"
        logging.debug("[DbMan][getConnectionString] Connection details: %s"% logStr)

        if ogr:
            return "PG: host=%s dbname=%s user=%s password=%s port=%s"%\
                    (dbhost, dbname,dbuser,dbpass,"5432")
        else:
            return "dbname='"+dbname+"' user='"+dbuser+"' host='"+dbhost+"' password='"+dbpass+"'"

    # Import

    def importShapeFile(self, filePath, dbSchema): 
        """import given file to database, ogr is used for data READING, psycopg2
        for data WRITING directly into PostGIS
        """
        conn = psycopg2.connect(self.getConnectionString())
        cur = conn.cursor()

        # shp2pgsql #
        logParam = "filePath='"+filePath+"', dbSchema='"+dbSchema+"'"
        logging.debug("[DbMan][importShapeFile] %s"% logParam)

        sqlBatch = ""

        try:
            pg_out = ogr.Open(self.getConnectionString(ogr=True)) # used only for checking
            # connect
            file_in = ogr.Open(filePath)

            if not file_in:
                # TODO: do not report whole file path, just file name
                raise LaymanError(500, "DbMan: could not open given file with OGR driver: %s" % filePath)

            # for each layer within the file
            # NOTE: in Shapefile, there is usually only one layer
            for layer_in in file_in:
                name_out = layer_in.GetName()
                # TODO: data exists, throw exception
                if pg_out.GetLayerByName(name_out):
                    pass

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
                    comma = ",\n"
                    if j+1 == fieldCount:
                        comma = ""
                    sqlBatch += '"'+fieldName.lower()+'" '+ field_type + comma
                    fields.append((fieldName, field_type))
                    j += 1
                sqlBatch += ");\n"
                sqlBatch += 'ALTER TABLE '+dbSchema+"."+name_out+' ADD PRIMARY KEY (gid);\n'

                # add geometry column
                sqlBatch += "".join(["SELECT AddGeometryColumn('",
                                      dbSchema,
                                      "','",
                                      name_out,
                                     "','geom','0','",
                                     self._getGeomType(layer_in.GetGeomType()),
                                     "',2);\n"])
                fields.append(("geom","geometry"))


                # create new table in database
                cur.execute(sqlBatch) # TODO check the success
                conn.commit()

                # database prepared, feed it
                sqlBatch = ""
                feature = layer_in.GetNextFeature()
                strfields = map(lambda field: '"%s"' % field[0], fields)
                # insert each feature into database table
                while feature:
                    vals = map(lambda field: "%s" % \
                            self._adjust_value(feature.GetField(field[0]),field[1]), fields[:-1])
                    geom = feature.GetGeometryRef().ExportToWkt()

                    # we have to convert polygons to multipolygons
                    if geom.find("POLYGON") == 0:
                        geom = geom.replace("POLYGON","MULTIPOLYGON(")
                        geom = geom+")"

                    # add geometry to values
                    vals.append("ST_AsText('"+geom+"')")

                    insert_str = 'INSERT INTO %(schema)s.%(table)s (%(columns)s) VALUES (%(values)s);' %\
                            ({
                                "schema":dbSchema,
                                "table": name_out,
                                "columns": ",".join(strfields).lower(),
                                "values": ",".join(vals)
                            })
                            
                    import sys
                    print >>sys.stderr, insert_str
                    cur.execute(insert_str)
                    feature = layer_in.GetNextFeature()
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

        if ftype == "real":
            if value == None:
                return "NULL"
            else:
                return str(float(value))
        elif tp == "integer":
            if value == None:
                return "NULL"
            else:
                return str(int(value))
        else:
            return "'%s'" % value

        # FIXME add more

    def _getGeomType(self,geomtype):
        """Return string representing propper geometry type, based on given input
        data ogr
        """

        if geomtype == ogr.wkbPolygon:
            return "MULTIPOLYGON"
        elif geomtype == ogr.wkbMultiPolygon:
            return "MULTIPOLYGON"
        elif geomtype == ogr.wkbPoint:
            return "POINT"
        elif geomtype == ogr.wkbLineString:
            return "LINESTRING"
        # FIXME: add more
