Ext4.define('HSRS.LayerManager.DataPanel', {

    extend: 'Ext4.grid.Panel',
    title: 'Data',

    requires: [
        'Ext4.data.JsonStore',
        'HSRS.LayerManager.DataPanel.Model',
        'HSRS.LayerManager.DataPanel.DataMenu'
    ],

    /**
     * @constructor
     */
    constructor: function(config) {

        myconfig = {};

        // Toolbar
        myconfig.tbar = Ext4.create('Ext4.toolbar.Toolbar', {
            items: [
                {   // Refresh
                    scope: this,
                    handler: this._onRefreshClicked,
                    cls: 'x-btn-icon',
                    tooltip: 'Refresh',
                    icon: HSRS.IMAGE_LOCATION + '/arrow_refresh.png'
                }
/*    ,            {   // Delete
                    scope: this,
                    handler: this._onDeleteClicked,
                    cls: 'x-btn-icon',
                    tooltip: 'Delete',
                    icon: HSRS.IMAGE_LOCATION + '/delete.png'
                }*/
            ]
        });

        // Store
        myconfig.store = Ext4.create('Ext4.data.Store', {
            model: 'HSRS.LayerManager.DataPanel.Model',
            groupField: 'schemaTitle',
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
                text: 'Schema',
                sortable: true,
                flex: 1,
                dataIndex: 'schemaTitle'
            },
            // data column
            {
                text: 'Name',
                sortable: true,
                flex: 1,
                dataIndex: 'name'
            }
            // type column
            {
                text: 'Type',
                sortable: true,
                flex: 1,
                dataIndex: 'type'
            }
        ];

        // grouping according to schemas
         var groupingFeature = Ext4.create('Ext4.grid.feature.Grouping', {
             groupHeaderTpl: '{name}',
            hideGroupedHeader: true
        });

        config = Ext4.Object.merge(myconfig, config);
        config.features = [groupingFeature];

        this.callParent(arguments);

        var makeMenu = function(view, record, elem, idx, e, opts) {

                // display file menu
                var menu = Ext4.create('HSRS.LayerManager.DataPanel.DataMenu', {
                    url: this.url,
                    record: record,
                    listeners: {
                        scope: this,

                        // file deleted listener will popup confirmation window
                        'datadeleted': function(record, evt) {
                            Ext4.MessageBox.confirm('Really delete selected data?',
                                    'Are you sure, you want to remove selected data? <br />', 
                                    function(btn, x, msg) {
                                        if (btn == 'yes') {/* TODO: lm.deleteData
                                            this.lm.deleteData(this.record.get('layer').name,
                                                                this.record.get('workspace'),
                                                               this.record.get('layer').title);*/
                                        }
                                    },
                                    {lm: this, record: record});

                                },
                        "datapublished":this._onDataPublished
                    }
            });

            menu.showAt(e.xy[0], e.xy[1], elem);
            Ext4.EventManager.stopEvent(e);
        };

        this.on('itemcontextmenu', makeMenu, this);
        this.on('itemclick', makeMenu, this);

        myconfig.store.load();

        this.addEvents("datapublished");
    },

    /**
     * send delete request
     */
    deleteData: function(schema, table) {
        var url = this.url + layer + '?usergroup='+ schema;

        Ext4.MessageBox.show({
               msg: 'Deleting data ['+table+'] ...',
               width:300,
               wait:true,
               waitConfig: {interval:200},
               icon: 'ext4-mb-download', //custom class in msg-box.html
               iconHeight: 50
           });

        Ext4.Ajax.request({
            method: 'DELETE',
            url: (HSRS.ProxyHost ? HSRS.ProxyHost + escape(url) : url),
            success: function() {
                Ext4.MessageBox.hide();
                Ext4.Msg.alert('Success', 'Deleting data succeeded');
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
    _onDataPublished: function(data) {
        this.fireEvent('datapublished', data);
    },

    /**
     * button refresh handler
     * @private
     */
     _onRefreshClicked: function() {
        this.store.load();
     }

});

