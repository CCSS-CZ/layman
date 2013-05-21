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
                },
                {
                    scope: this,
                    handler: this._onDeleteClicked,
                    cls: 'x-btn-icon',
                    tooltip: 'Delete layer',
                    icon: HSRS.IMAGE_LOCATION + '/delete.png'
                }
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
                dataIndex: 'featureType',
                tpl: '{featuretype.title}'
            }
        ];

        // grouping according to workspaces
         var groupingFeature = Ext4.create('Ext4.grid.feature.Grouping', {
             groupHeaderTpl: '{name}',
            hideGroupedHeader: true
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

                        // file deleted listener will popup confirmation window
                        'layerdeleted': function(record, evt) {
                            Ext4.MessageBox.confirm('Really remove selected layer?',
                                    'Are you sure, you want to remove selected layer? <br />', 
                                    function(btn, x, msg) {
                                        if (btn == 'yes') {
                                            this.lm.deleteLayer(this.record.get('layer').name,
                                                                this.record.get('workspace'));
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
    },

    /**
     * send delete request
     *
     * @function
     * @param layer {String}  layer name.
     * @param layer {workspace} ws name.
     */
    deleteLayer: function(layer,ws) {
        var url = this.url + layer + '?usergroup='+ ws;
        Ext4.Ajax.request({
            method: 'DELETE',
            url: (HSRS.ProxyHost ? HSRS.ProxyHost + escape(url) : url),
            success: function() {
                this.store.load();
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
