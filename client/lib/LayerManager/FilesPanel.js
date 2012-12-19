
Ext4.define("HSRS.LayerManager.FilesPanel", {
    
    requires: [
        "Ext4.data.JsonStore",
        "HSRS.LayerManager.FilesPanel.FileUploader",
        "HSRS.LayerManager.FilesPanel.FileMenu"
    ],

    extend: "Ext4.grid.Panel",
    title: "Files",
    url: "",

    /**
     * @constructor
     */
    constructor: function(config) {
        myconfig = {};
        myconfig.tbar = Ext4.create("Ext4.toolbar.Toolbar", {
            items: [
                {
                    //text: 'Refresh',
                    scope: this,
                    handler:  this._onRefreshClicked,
                    cls: 'x-btn-icon',
                    tooltip: 'Refresh file list',
                    icon: HSRS.IMAGE_LOCATION+"/arrow_refresh.png"
                },
                {
                    scope: this,
                    handler:  this._onUploadClicked,
                    cls: 'x-btn-icon',
                    tooltip: 'Upload new file',
                    icon: HSRS.IMAGE_LOCATION+"/add.png"
                },
                {
                    scope: this,
                    handler:  this._onDeleteClicked,
                    cls: 'x-btn-icon',
                    tooltip: 'Delete file',
                    icon: HSRS.IMAGE_LOCATION+"/delete.png"
                }
            ]
        });

        /*
         * model and store
         */
        Ext4.define('HSRS.LayerManager.FilesPanel.Model', {
                extend: 'Ext4.data.Model',
                fields: [
                    {name: 'name',     type: 'string'},
                    {name: 'size',     type: 'integer'},
                    //{name: 'prj',      type: 'string'},
                    {name: 'date',      type: 'string'},
                    {name: 'mimetype', type: 'string'}
                ]
        }); 
        
        myconfig.store = Ext4.create("Ext4.data.JsonStore", {
            model: 'HSRS.LayerManager.FilesPanel.Model',
            //autoLoad: true,
            //autoSync: true,
            proxy: {
                type: "ajax",
                url: config.url,
                reader: {
                    type: 'json',
                    idProperty: 'name'
                }
            }
        });
        myconfig.store.load();

        myconfig.multiSelect = true;

        myconfig.autoScroll =  true;
        myconfig.anchor = "100%";

        myconfig.columns = [ 
            // icon column
            {
                xtype: 'templatecolumn',
                text: ' ',
                width: 22,
                flex: 0,
                sortable: true,
                dataIndex: 'mimetype',
                align: 'center',
                //add in the custom tpl for the rows
                tpl: Ext4.create('Ext4.XTemplate', '{mimetype:this.formatType}', {
                    formatType: function(v) {
                        var img = "type_file.png";
                        switch(v) {
                            case "application/x-zipped-shp":
                                img = "type_shp.png";
                            break;
                        }

                        return '<img src="'+HSRS.IMAGE_LOCATION+img+'" />';
                    }
                })
            },
            // filename column
            {
                text: "Name",
                sortable: true,
                flex:1,
                dataIndex: "name"
            },
            // file type
            {
                xtype: 'templatecolumn',
                width: 35,
                text: "Type",
                flex: 0,
                sortable: true,
                dataIndex: "mimetype",
                tpl: Ext4.create('Ext4.XTemplate', '{mimetype:this.formatType}', {
                    formatType: function(v) {
                        switch(v) {
                            case "application/x-zipped-shp":
                                return  "SHP";
                            break;
                        }
                    }
                })
            },
            // file size
            {
                xtype: 'templatecolumn',
                text: "Size",
                sortable: true,
                flex: 0,
                width: 45,
                dataIndex: "size",
                tpl: Ext4.create('Ext4.XTemplate', '{size:this.formatSize}', {
                    formatSize: function(v) {
                        return String(v);
                    }
                })
            },
            // date
            {
                xtype: 'templatecolumn',
                text: "Date",
                sortable: true,
                flex: 0,
                width: 100,
                dataIndex: "date",
                tpl: Ext4.create('Ext4.XTemplate', '{date:this.formatDate}', {
                    formatDate: function(v) {
                        return String(v);
                    }
                })
            }
        ];

        config = Ext.Object.merge(myconfig, config);
        this.callParent([config]);
        this.addEvents("filepublished");

        this.on("itemcontextmenu",function(view, record, elem, idx, e, opts) {
                this.getFileDetail(record.get("name"),function(r) {
                    var menu = Ext4.create("HSRS.LayerManager.FilesPanel.FileMenu", {
                        data: Ext4.JSON.decode(r.responseText),
                        listeners: {
                            "filepublished": this._onFilePublished,
                            scope: this
                        }
                });
                
                menu.showAt(e.xy[0],e.xy[1],elem);
                }, this);
                Ext4.EventManager.stopEvent(e);
            },
            this
        );
    },

    /**
     * get file details
     * @function
     * @name HSRS.LayerManager.FilesPanel.getFileDetail
     * @param name {String}
     * @param caller {Function}
     * @param scope {Object}
     */
    getFileDetail: function(name, caller, scope) {
        Ext4.Ajax.request({
            url:"file_detail.json",
            params: {
                name: name
            },
            success: caller,
            scope: scope
        });
    },

    /**
     * button refresh handler
     * @private
     */
     _onRefreshClicked: function() {
        this.store.load(); 
     },

    /**
     * button upload handler
     * @private
     */
     _onUploadClicked: function() {
        var fileUploader = Ext.create("HSRS.LayerManager.FilesPanel.FileUploader",{
            url:"upload_file_exists.html",
            listeners: {
                scope: fileUploader,
                "filesaved": function(){this._win.close();}
            }
        });

        fileUploader._win = Ext.create("Ext.window.Window", {
            title: "File upload",
            height: 150,
            width: 400,
            layout: "fit",
            items: [
                fileUploader
            ]
        });
        fileUploader._win.show();

     },

    /**
     * delete selected files
     * @private
     * @function
     */
    _onDeleteClicked: function() {
        var records = this.getSelectionModel().getSelection();

        if (records.length > 0) {
            Ext4.MessageBox.confirm("Really remove selected files?",
                    "Are you sure, you want to remove selected files? <br />"+
                    records.map(function(r){return r.get("name");}).join("<br />"));
        }
    },

    /**
     * file published handler
     * @private
     * @function
     */
    _onFilePublished: function(data) {
        this.fireEvent("filepublished",data);
    }
});
