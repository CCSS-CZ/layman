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
	type varchar(255), -- vector, raster
	datagroup varchar (255), -- schema or directory of the data source
	dataname varchar (255), -- data source name (table, view or file)
	constraint layers_group_name primary key (usergroup, name)
);

-- Evidence of data sources: 
--   Vectors - tables and views in db
--   Rasters - files in the filesystem
create table layman.data (
	-- id int not null auto_increment,
	dataname varchar(255) not null, -- table or view or file
	datagroup varchar(255) not null, -- schema or directory
	owner varchar(255), -- owner of the layer
	type varchar(255), -- vector, raster
	updated timestamp, -- time of last update
	constraint data_group_name primary key (usergroup, name)
);

-- some examples:

insert into layman.layers (name, usergroup, owner, type, datagroup, dataname)
values ('jmeno', 'skupina', 'majitel', 'vector', 'skupina', 'jmeno_00');

delete from layman.layers 
where name='jmeno' and usergroup='skupina';

