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

        var url = config.url + (config.url[config.url.length - 1] == '/' ? '' : '/') + 'fileman/';
        this.filesPanel = Ext4.create('HSRS.LayerManager.FilesPanel', {
            //url: config.url,
            url: url,
            listeners: {
                scope: this,
                'filepublished': this._onFilePublished,
                'fileupdated': this._onLayerUpdated
            },
            flex: 1
        });

        url = config.url + (config.url[config.url.length - 1] == '/' ? '' : '/') + 'layed/';

        this.layersPanel = Ext4.create('HSRS.LayerManager.LayersPanel', {
            url: url,
            flex: 1,
            listeners: {
                scope: this,
                'layerupdated': this._onLayerUpdated
            }
        });

        this.layersPanel.store.on('load', this._onLayersLoaded, this);

        config.items = [this.filesPanel, this.layersPanel];

        this.callParent(arguments);
    },

    /**
     * handler
     * @private
     * @function
     */
    _onFilePublished: function(data) {
        Ext4.Msg.alert('Success', 'File ['+ data.fileName + '] published');
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

            msg += "<br /> Since new data was loaded, please make sure, layer style is still working";
        }
        Ext4.Msg.alert('Success', msg);
        this.layersPanel.store.load();
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
