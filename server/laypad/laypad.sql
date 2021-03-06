-- LayPad - a notepad for layman.
-- All addiotional info related to published layers.

-- Create schema
create schema layman;

-- Evidence of GeoServer Layers
create table layman.layers (
	-- id int not null auto_increment,
	layername varchar(255) not null, -- layer name
	layergroup varchar(255) not null, -- workspace
    layertitle varchar(255), -- layer title
	owner varchar(255), -- owner of the layer
	layertype varchar(255), -- vector, raster 
	datagroup varchar (255), -- schema or directory of the data source
	dataname varchar (255), -- data source name (table, view or file)
    datatype varchar (255), -- table, view, file
    vectortype varchar (255), -- point, line, polygon (NULL for rasters)
	constraint layers_group_name primary key (layergroup, layername)
);

-- Evidence of data sources: 
--   Vectors - tables and views in db
--   Rasters - files in the filesystem
create table layman.data (
	-- id int not null auto_increment,
	dataname varchar(255) not null, -- table or view or file
	datagroup varchar(255) not null, -- schema or directory
	owner varchar(255), -- owner of the layer
	datatype varchar(255), -- table, view, file
    layertype varchar(255), -- vector, raster
	updated timestamp, -- time of last update
	constraint datagroup_dataname primary key (datagroup, dataname)
);

-- some examples:

insert into layman.layers (layername, layergroup, layertitle, owner, layertype, datagroup, dataname, datatype, vectortype)
values ('jmeno', 'skupina', 'titulek', 'majitel', 'vector', 'skupina', 'jmeno_00', 'table', 'polygon');

delete from layman.layers 
where layername='jmeno' and layergroup='skupina';

-- CKAN resources info:
create table layman.ckanRes (
    ckan varchar(255) not null, -- CKAN URL
    format varchar(255) not null, -- json, shp, kml...
    count integer, -- number of resources of given format
    ts timestamp, -- when this was true
    constraint ckan_format primary key (ckan, format) 
);

