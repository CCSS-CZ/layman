Ext4.define('HSRS.LayerManager.LayersPanel', {

    extend: 'Ext4.grid.Panel',
    title: 'Layers',

    requires: [
        'Ext4.data.JsonStore',
        'HSRS.LayerManager.LayersPanel.Model',
        'HSRS.LayerManager.LayersPanel.LayerMenu'
    ],

    /**
     * @constructor
     */
    constructor: function(config) {

        myconfig = {};

        myconfig.tbar = Ext4.create('Ext4.toolbar.Toolbar', {
            items: [
                {
                    //text: 'Refresh',
                    scope: this,
                    handler: this._onRefreshClicked,
                    cls: 'x-btn-icon',
                    tooltip: 'Refresh file list',
                    icon: HSRS.IMAGE_LOCATION + '/arrow_refresh.png'
                }/*,
                {
                    scope: this,
                    handler: this._onDeleteClicked,
                    cls: 'x-btn-icon',
                    tooltip: 'Delete layer',
                    icon: HSRS.IMAGE_LOCATION + '/delete.png'
                }*/
            ]
        });

        myconfig.store = Ext4.create('Ext4.data.Store', {
            model: 'HSRS.LayerManager.LayersPanel.Model',
            groupField: 'wstitle',
            //autoLoad: true,
            //autoSync: true,
            proxy: {
                type: 'ajax',
                url: (HSRS.ProxyHost ? HSRS.ProxyHost + escape(config.url) : config.url),
                reader: {
                    type: 'json'
                }
            }
        });

        myconfig.multiSelect = true;
        myconfig.autoScroll = true;
        myconfig.anchor = '100%';


        myconfig.columns = [
            // ws column
            {
                text: 'Workspace',
                sortable: true,
                flex: 1,
                dataIndex: 'wstitle'
            },
            // icon column
            {
                xtype: 'templatecolumn',
                text: ' ',
                width: 22,
                flex: 0,
                sortable: true,
                dataIndex: 'layer',
                align: 'center',
                //add in the custom tpl for the rows
                tpl: Ext4.create('Ext4.XTemplate', '{layer:this.formatIcon}', {
                    formatIcon: function(v) {
                        return '<img src="' + HSRS.IMAGE_LOCATION + v.type.toLowerCase() + '-type.png" />';
                    }
                })
            },
            // layer column
            {
                text: 'Layer',
                xtype: 'templatecolumn',
                sortable: true,
                flex: 1,
                dataIndex: 'layerData',
                tpl: Ext4.create('Ext4.XTemplate', '{layerData:this.formatTitle}', {
                    formatTitle: function(v) {
                        return v.title;
                    }
                })
            }
        ];

        // grouping according to workspaces
        var groupingFeature = Ext4.create('Ext4.grid.feature.Grouping', {
            groupHeaderTpl: '{name}',
            hideGroupedHeader: true,
            collapsible: false
        });

        config = Ext4.Object.merge(myconfig, config);
        config.features = [groupingFeature];

        this.callParent(arguments);

        var makeMenu = function(view, record, elem, idx, e, opts) {

                // display file menu
                var menu = Ext4.create('HSRS.LayerManager.LayersPanel.LayerMenu', {
                    url: this.url,
                    record: record,
                    listeners: {
                        scope: this,

                        // layer deleted listener will popup confirmation window
                        'layerdeleted': function(record, evt) {
                            Ext4.MessageBox.confirm('Really remove selected layer?',
                                    'Are you sure, you want to remove selected layer and the underlying data? <br />', 
                                    function(btn, x, msg) {
                                        if (btn == 'yes') {
                                            this.lm.deleteLayer(this.record.get('layer').name,
                                                                this.record.get('workspace'),
                                                                this.record.get('layer').title,
                                                                true); // deleteTable = true
                                        }
                                    },
                                    {lm: this, record: record});

                                },

                        'layeronlydeleted': function(record, evt) {
                            Ext4.MessageBox.confirm('Really remove selected layer?',
                                    'Are you sure, you want to remove selected layer? <br />', 
                                    function(btn, x, msg) {
                                        if (btn == 'yes') {
                                            this.lm.deleteLayer(this.record.get('layer').name,
                                                                    this.record.get('workspace'),
                                                                    this.record.get('layer').title,
                                                                    false); // deleteTable = false
                                        }
                                    },
                                    {lm: this, record: record});

                                },

                        "layerupdated":this._onLayerUpdated
                    }
            });

            menu.showAt(e.xy[0], e.xy[1], elem);
            Ext4.EventManager.stopEvent(e);
        };

        this.on('itemcontextmenu', makeMenu, this);
        this.on('itemclick', makeMenu, this);

        myconfig.store.load();

        this.addEvents("layerupdated");
        this.addEvents("layerdeleted");
    },

    /**
     * send delete request
     *
     * @function
     * @param layer {String}  layer name.
     * @param layer {workspace} ws name.
     */
    deleteLayer: function(layer, ws, title, deleteTable) {
        var url = this.url + layer + '?usergroup='+ ws;

        if (deleteTable == false) {
            url = url + "&deleteTable=false"
        }

        title = title || layer;

        Ext4.MessageBox.show({
               msg: 'Deleting layer ['+title+'] ...',
               width:300,
               wait:true,
               waitConfig: {interval:200},
               icon: 'ext4-mb-download', //custom class in msg-box.html
               iconHeight: 50
           });

        Ext4.Ajax.request({
            method: 'DELETE',
            url: (HSRS.ProxyHost ? HSRS.ProxyHost + escape(url) : url),
            success: function(form, action) {
                Ext4.MessageBox.hide();
                Ext4.Msg.alert('Success', 'Deleting layer succeeded');
                this.store.load();
                this.fireEvent('layerdeleted');
            },
            failure: function(form, action) {
                Ext4.MessageBox.hide();
                var obj;
                try {
                    obj = Ext4.decode(form.responseText);
                }
                catch (E) {
                    obj = {message: ''};
                }
                Ext4.Msg.alert('Failed', 'Delete error' +
                '<br />' + obj.message);
            },
            scope: this
        });
    },

    /**
     * file published handler
     * @private
     * @function
     */
    _onLayerUpdated: function(data) {
        this.fireEvent('layerupdated', data);
    },

    /**
     * button refresh handler
     * @private
     */
     _onRefreshClicked: function() {
        this.store.load();
     }

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
