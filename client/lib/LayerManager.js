/*
    LayMan - the Layer Manager

    Copyright (C) 2016 Czech Centre for Science and Society
    Authors: Jachym Cepicky, Karel Charvat, Stepan Kafka, Michal Sredl, Premysl Vohnout
    Mailto: sredl@ccss.cz, charvat@ccss.cz

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

Ext4.define('HSRS.LayerManager', {
    /*
     * configuration
     */
    extend: 'Ext.panel.Panel',
    requires: [
        'HSRS.LayerManager.FilesPanel',
        'HSRS.LayerManager.LayersPanel'
    ],


    showCkan: true,
    ckanPanel: undefined,

    showFiles: true,
    filesPanel: undefined,

    showData: true,
    dataPanel: undefined,

    layersPanel: undefined,

    /**
     * @constructor
     */
    constructor: function(config) {
        config.layout = {
            type: 'hbox',
            reserveScrollbar: true,
            align: 'stretch'
        };

        // Detect what panels we want
        if ( ("showCkan" in config) && !(config.showCkan) )
           this.showCkan = false; 
        if ( ("showFiles" in config) && !(config.showFiles) )
           this.showFiles = false; 
        if ( ("showData" in config) && !(config.showData) )
           this.showData = false; 

        // CKAN Panel
        if (this.showCkan) {
            url = config.url + (config.url[config.url.length - 1] == '/' ? '' : '/') + 'ckan/';
            this.ckanPanel = Ext4.create('HSRS.LayerManager.CkanPanel', {
                url: url,
                flex: 1,
                listeners: {
                    scope: this,
                    'ckandownloaded': this._onCkanDownloaded
                }
            });
        }

        // Files Panel
        var url = config.url + (config.url[config.url.length - 1] == '/' ? '' : '/') + 'fileman/';
        var srid = config.srid;
        this.filesPanel = Ext4.create('HSRS.LayerManager.FilesPanel', {
            //url: config.url,
            url: url,
            srid: srid,
            flex: 1,
            listeners: {
                scope: this,
                'filepublished': this._onFilePublished,
                'fileupdated': this._onLayerUpdated
            }
        });

        // Data Panel
        url = config.url + (config.url[config.url.length - 1] == '/' ? '' : '/') + 'data/';
        this.dataPanel = Ext4.create('HSRS.LayerManager.DataPanel', {
            url: url,
            flex: 1,
            listeners: {
                scope: this,
                'datapublished': this._onDataPublished
            }
        });

        // Layers Panel
        url = config.url + (config.url[config.url.length - 1] == '/' ? '' : '/') + 'layed/';
        this.layersPanel = Ext4.create('HSRS.LayerManager.LayersPanel', {
            url: url,
            flex: 1,
            listeners: {
                scope: this,
                'layerupdated': this._onLayerUpdated,
                'layerdeleted': this._onLayerDeleted
            }
        });

        this.layersPanel.store.on('load', this._onLayersLoaded, this);

        // Items
        config.items = []        

        if ( this.showCkan )
            config.items.push(this.ckanPanel);

        if ( this.showFiles )
            config.items.push(this.filesPanel);  

        if ( this.showData )
            config.items.push(this.dataPanel);

        config.items.push(this.layersPanel);

        this.callParent(arguments);
    },

    _onCkanDownloaded: function(data) {
        //Ext4.Msg.alert(HS.i18n('Success'), HS.i18n('Dataset downloaded') + ' ['+ (data.title || data.name) + ']');
        this.filesPanel.store.load();
    },

    /**
     * handler
     * @private
     * @function
     */
    _onFilePublished: function(data) {
        Ext4.Msg.alert(HS.i18n('Success'), HS.i18n('File published') + ' ['+ data.fileName + ']');
        this.dataPanel.store.load();
        this.layersPanel.store.load();
    },

    _onDataPublished: function(data) {
        Ext4.Msg.alert(HS.i18n('Success'), HS.i18n('Data published') + ' ['+ (data.title || data.view) + ']');
        this.layersPanel.store.load();
    },

    /**
     * handler
     * @private
     * @function
     */
    _onLayerUpdated: function(data) {
        var msg = HS.i18n('Layer updated') + ' ['+ (data.title || data.name) + ']';
        if (data.publish_as != "newfile") {

            msg += "<br />"+ HS.i18n("As new data was loaded, please check the layer style if it still works as expected.");
        }
        Ext4.Msg.alert(HS.i18n('Success'), msg);
        this.layersPanel.store.load();
    },

    _onLayerDeleted: function() {
        this.dataPanel.store.load();        
    },

    /**
     * handler
     * @private
     * @function
     */
    _onLayersLoaded: function() {
        var groups = this.layersPanel.store.getGroups().map(function(g) {
                return [g.children[0].get('workspace'), g.children[0].get('wstitle')];
        });
        this.filesPanel.setGroups(groups);
    }

});
