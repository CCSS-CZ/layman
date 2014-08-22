Ext4.define('HSRS.LayerManager', {
    /*
     * configuration
     */
    extend: 'Ext.panel.Panel',
    requires: [
        'HSRS.LayerManager.FilesPanel',
        'HSRS.LayerManager.LayersPanel'
    ],

    /**
     * @name HSRS.LayerManager.filesPanel
     * @type HSRS.LayerManager.FilesPanel
     */
    filesPanel: undefined,

    dataPanel: undefined,

    /**
     * @name HSRS.LayerManager.filesPanel
     * @type HSRS.LayerManager.FilesPanel
     */
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

        // Languages, save to cookie
        HS.setLang(HS.getLang(), true);

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

        config.items = [this.filesPanel, this.dataPanel, this.layersPanel];

        this.callParent(arguments);
    },

    /**
     * handler
     * @private
     * @function
     */
    _onFilePublished: function(data) {
        Ext4.Msg.alert('Success', 'File ['+ data.fileName + '] published');
        this.dataPanel.store.load();
        this.layersPanel.store.load();
    },

    _onDataPublished: function(data) {
        Ext4.Msg.alert('Success', 'Data ['+ (data.title || data.view) + '] published');
        this.layersPanel.store.load();
    },

    /**
     * handler
     * @private
     * @function
     */
    _onLayerUpdated: function(data) {
        var msg = 'Layer ['+ (data.title || data.name) + '] updated';
        if (data.publish_as != "newfile") {

            msg += "<br /> As new data was loaded, please check the layer style if it still works as expected.";
        }
        Ext4.Msg.alert('Success', msg);
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
