Ext4.define('HSRS.LayerManager.CkanPanel', {

    extend: 'Ext4.grid.Panel',
    title: HS.i18n('CKAN'),

    requires: [
        'Ext4.data.JsonStore',
        'HSRS.LayerManager.CkanPanel.Model' /*,
        'HSRS.LayerManager.CkanPanel.CkanMenu' */
    ],

    /**
     * @constructor
     */
    constructor: function(config) {

        myconfig = {};

        // Store
        myconfig.store = Ext4.create('Ext4.data.Store', {
            model: 'HSRS.LayerManager.CkanPanel.Model',
            groupField: 'organizationTitle',
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
            // org column
            {
                text: HS.i18n('Organization'),
                sortable: true,
                flex: 1,
                dataIndex: 'organizationTitle'
            },
            // dataset column
            {
                text: HS.i18n('Dataset'),
                sortable: true,
                flex: 1,
                dataIndex: 'title'
            },
            // description column
            {
                text: HS.i18n('Description'),
                sortable: true,
                flex: 1,
                dataIndex: 'notes'
            }
        ];

        // grouping according to organizations
        var groupingFeature = Ext4.create('Ext4.grid.feature.Grouping', {
            groupHeaderTpl: '{name}',
            hideGroupedHeader: true,
            collapsible: false
        });

        config = Ext4.Object.merge(myconfig, config);
        config.features = [groupingFeature];

        this.callParent(arguments);
/*
        var makeMenu = function(view, record, elem, idx, e, opts) {

                // display file menu
                var menu = Ext4.create('HSRS.LayerManager.DataPanel.DataMenu', {
                    url: this.url,
                    record: record,
                    listeners: {
                        scope: this,

                        // file deleted listener will popup confirmation window
                        'datadeleted': function(record, evt) {
                            Ext4.MessageBox.confirm(HS.i18n('Really delete selected data?'),
                                    HS.i18n('Are you sure, you want to remove selected data?') +' <br />', 
                                    function(btn, x, msg) {
                                        if (btn == 'yes') {/* TODO: lm.deleteData
                                            this.lm.deleteData(this.record.get('layer').name,
                                                                this.record.get('workspace'),
                                                               this.record.get('layer').title);* /
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
*/
        myconfig.store.load();

//        this.addEvents("datapublished");
    } //,


    /**
     * file published handler
     * @private
     * @function
     */
/*    _onDataPublished: function(data) {
        this.fireEvent('datapublished', data);
    },*/

    /**
     * button refresh handler
     * @private
     */
/*     _onRefreshClicked: function() {
        this.store.load();
     },*/

});

