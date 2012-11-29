Ext4.define("HSRS.LayerManager", {
    /*
     * configuration
     */
    extend: "Ext.panel.Panel",
    requires: [
        "HSRS.LayerManager.FilesPanel",
        "HSRS.LayerManager.LayersPanel"
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
            type:"hbox",
            reserveScrollbar: true,
            align: "stretch"
        };

        this.filesPanel = Ext4.create("HSRS.LayerManager.FilesPanel", {
            url: config.url,
            
            flex: 1
        });
        this.layersPanel = Ext4.create("HSRS.LayerManager.LayersPanel", {
            flex: 1
        });

        config.items = [this.filesPanel, this.layersPanel];

        this.callParent(arguments);
    }
});
