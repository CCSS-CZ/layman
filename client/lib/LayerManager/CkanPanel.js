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

        // Toolbar
        myconfig.tbar = Ext4.create('Ext4.toolbar.Toolbar', {
            items: [
                {   // Refresh
                    scope: this,
                    handler: this._onRefreshClicked,
                    cls: 'x-btn-icon',
                    tooltip: HS.i18n('Refresh'),
                    icon: HSRS.IMAGE_LOCATION + '/arrow_refresh.png'
                }
            ]
        });


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

        var makeMenu = function(view, record, elem, idx, e, opts) {

            // display ckan menu
            var menu = Ext4.create('HSRS.LayerManager.CkanPanel.CkanMenu', {
                url: this.url,
                record: record,
                listeners: {
                    scope: this,
                    'copytofiles': function(record, evt) {}
                    }
                });

            menu.showAt(e.xy[0], e.xy[1], elem);
            Ext4.EventManager.stopEvent(e);
        };

        this.on('itemcontextmenu', makeMenu, this);
        this.on('itemclick', makeMenu, this);

        myconfig.store.load();

        this.addEvents("ckandownloaded");
    },


    /**
     * ckan download handler
     * @private
     * @function
     */
    _onCkanDownloaded: function(data) {
        this.fireEvent('ckandownloaded', data);
    },

    /**
     * button refresh handler
     * @private
     */
     _onRefreshClicked: function() {
        this.store.load();
     }

});

