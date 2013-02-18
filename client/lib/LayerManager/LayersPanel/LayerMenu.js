/**
 * License: ...
 * @author: Jachym
 */

Ext4.define("HSRS.LayerManager.LayersPanel.LayerMenu", {
    
    extend: "Ext4.menu.Menu",

    requires:[],

    layer: undefined,
    url: undefined,
    record: undefined,
    
    /**
     * @constructor
     */
    constructor: function(config) {
        config.title = config.record.get("name");
        config.width = 200;
        config.plain = true;

        this.url = config.url.replace(/\/$/,config.record.get("name"));

        config.items = [
            {
                text: "Delete",
                icon: HSRS.IMAGE_LOCATION+"/delete.png",
                scope: this,
                handler: this._onDeleteClicked
            }
        ];

        this.callParent(arguments);

        this.addEvents("layerdeleted");
    },

    /**
     * delete handler
     * @private
     */
    _onDeleteClicked: function() {
        this.fireEvent("layerdeleted",this.record);
    }
});
