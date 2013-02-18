Ext4.define("HSRS.LayerManager.LayersPanel", {
    
    extend: "Ext.grid.Panel",
    title: "Layers",

    requires: [
        "Ext4.data.JsonStore",
        "HSRS.LayerManager.LayersPanel.Model",
        "HSRS.LayerManager.LayersPanel.LayerMenu"
    ],

    /**
     * @constructor
     */
    constructor: function(config) {

        myconfig = {};
        
        myconfig.store = Ext4.create("Ext4.data.JsonStore", {
            model: 'HSRS.LayerManager.LayersPanel.Model',
            //autoLoad: true,
            //autoSync: true,
            proxy: {
                type: "ajax",
                url: (HSRS.ProxyHost ? HSRS.ProxyHost+escape(config.url):config.url),
                reader: {
                    type: 'json',
                    root: "layers.layer",
                    idProperty: 'name'
                }
            }
        });
        myconfig.store.load();

        myconfig.multiSelect = true;
        myconfig.autoScroll =  true;
        myconfig.anchor = "100%";

        myconfig.columns = [ 
            // layer column
            {
                text: "Name",
                sortable: true,
                flex:1,
                dataIndex: "name"
            }
        ];

        config = Ext.Object.merge(myconfig, config);

        this.callParent(arguments);

        var makeMenu = function(view, record, elem, idx, e, opts) {

                // display file menu
                var menu = Ext4.create("HSRS.LayerManager.LayersPanel.LayerMenu", {
                    url: this.url,
                    record: record,
                    listeners: {
                        scope:this,

                        // file deleted listener will popup confirmation window
                        "layerdeleted": function(record, evt) {
                            Ext4.MessageBox.confirm("Really remove selected layer?",
                                    "Are you sure, you want to remove selected file? <br />"+
                                    record.get("name"),
                                    function(btn, x, msg){
                                        if (btn == "yes") {
                                            this.lm.deleteLayer(this.record.get("name"));
                                        }
                                    },
                                    {lm: this, record: record});

                                }
                    }
            });
            
            menu.showAt(e.xy[0],e.xy[1],elem);
            Ext4.EventManager.stopEvent(e);
        };

        this.on("itemcontextmenu",makeMenu, this);
        this.on("itemclick",makeMenu, this);
    },

    /**
     * send delete request
     *
     * @function
     * @param layer {String}  layer name
     */
    deleteLayer: function(layer) {
        var url = this.url+layer;
        console.log(this.url);
        Ext4.Ajax.request({
            method: "DELETE",
            url: (HSRS.ProxyHost ? HSRS.ProxyHost+escape(url):url),
            success: function() {
                console.log("####",arguments);
            },
            scope: this
        });
        this.store.load(); 
    },

    /**
     * get file details
     * @function
     * @name HSRS.LayerManager.FilesPanel.getFileDetail
     * @param name {String}
     * @param caller {Function}
     * @param scope {Object}
     */
    //getLayerDetail: function(name, caller, scope) {
    //    var url = this.url.replace(/\/$/,"")+"/detail/"+name;
    //    Ext4.Ajax.request({
    //        url: (HSRS.ProxyHost ? HSRS.ProxyHost+escape(url):url),
    //        success: caller,
    //        scope: scope
    //    });
    //}
});
