Ext4.define('HSRS.LayerManager.DataPanel', {

    extend: 'Ext4.grid.Panel',
    title: HS.i18n('Data'),

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
                    tooltip: HS.i18n('Refresh'),
                    icon: HSRS.IMAGE_LOCATION + '/arrow_refresh.png'
                },
                /* {   // Delete
                    scope: this,
                    handler: this._onDeleteClicked,
                    cls: 'x-btn-icon',
                    tooltip: 'Delete',
                    icon: HSRS.IMAGE_LOCATION + '/delete.png'
                },*/
                {   // Sync
                    scope: this,
                    handler: this._onSyncClicked,
                    text: HS.i18n('Sync'),
                    tooltip: HS.i18n('Synchronise with database')
                } 
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
                text: HS.i18n('Schema'),
                sortable: true,
                flex: 1,
                dataIndex: 'schemaTitle'
            },
            // data column
            {
                text: HS.i18n('Name'),
                sortable: true,
                flex: 1,
                dataIndex: 'name'
            },
            // type column
            {
                text: HS.i18n('Type'),
                sortable: true,
                flex: 1,
                dataIndex: 'type'
            }
        ];

        // grouping according to schemas
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
                var menu = Ext4.create('HSRS.LayerManager.DataPanel.DataMenu', {
                    url: this.url,
                    record: record,
                    listeners: {
                        scope: this,
                        'datapublished': this._onDataPublished,

                        // file deleted listener will popup confirmation window
                        'datadeleted': function(record, evt) {
                            Ext4.MessageBox.confirm(HS.i18n('Really delete selected data?'),
                                    HS.i18n('Are you sure, you want to remove selected data?') +' <br />', 
                                    function(btn, x, msg) {
                                        if (btn == 'yes') {/* TODO: lm.deleteData
                                            this.lm.deleteData(this.record.get('layer').name,
                                                                this.record.get('workspace'),
                                                               this.record.get('layer').title);*/
                                        }
                                    },
                                    {lm: this, record: record});

                                },

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

    _onSyncClicked: function() {
        var url = this.url + "sync";

        Ext4.Ajax.request({
            scope: this,
            method: 'GET',
            url: (HSRS.ProxyHost ? HSRS.ProxyHost + escape(url) : url),
            success: function(form, action) {
                var obj;
                try {
                    obj = Ext4.decode(form.responseText);
                }
                catch (E) {
                    obj = {message: ''};
                }
                Ext4.Msg.alert(HS.i18n('Success'), HS.i18n('Data of all your groups has been synchronised') +
                     '<br />' + obj.message);
                this.store.load();
            },
            failure: function(form, action) {
                var obj;
                try {
                    obj = Ext4.decode(form.responseText);
                }
                catch (E) {
                    obj = {message: ''};
                }
                Ext4.Msg.alert(HS.i18n('Failed'), HS.i18n('Synchronisation of data failed') +
                    '<br />' + obj.message);
            }
        });
    }

    /**
     * send delete request
     */
    deleteData: function(schema, table) {
        var url = this.url + layer + '?usergroup='+ schema;

        Ext4.MessageBox.show({
               msg: HS.i18n('Deleting data') + ' ['+table+'] ...',
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
                Ext4.Msg.alert(HS.i18n('Success'), HS.i18n('Deleting data succeeded'));
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
     },
    
    _onCkanClicked: function() {

        // Open CKAN window

        url = this.url.replace('data','ckan');
        var ckanPanel = Ext4.create('HSRS.LayerManager.CkanPanel', {
            url: url
        });

        ckanPanel._win = Ext4.create('Ext4.window.Window', {
            title: HS.i18n('CKAN'),
            items: [ckanPanel]
        });

        ckanPanel.on('canceled', ckanPanel._win.close, ckanPanel._win);

        ckanPanel._win.show();
    }

});

