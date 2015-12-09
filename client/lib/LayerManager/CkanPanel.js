Ext4.define('HSRS.LayerManager.CkanPanel', {

    extend: 'Ext4.grid.Panel',
    title: HS.i18n('CKAN'),

    requires: [
        'Ext4.data.JsonStore',
        'HSRS.LayerManager.CkanPanel.Model',
        'HSRS.LayerManager.CkanPanel.CkanMenu' 
    ],

    /**
     * @constructor
     */
    constructor: function(config) {

        myconfig = {};

        var itemsPerPage = 30;
        var defaultCkanUrl = "http://ckan-otn-dev.intrasoft-intl.com/";

        // Store
        myconfig.store = Ext4.create('Ext4.data.Store', {
            // model: 'HSRS.LayerManager.CkanPanel.PackageModel',
            model: 'HSRS.LayerManager.CkanPanel.ResourceModel',
            // groupField: 'organizationTitle',
            pageSize: itemsPerPage,
            proxy: {
                type: 'ajax',
                url: (HSRS.ProxyHost ? HSRS.ProxyHost + escape(config.url) : config.url),
                reader: {
                    type: 'json',
                    root: 'rows',
                    totalProperty: 'results'
                },
                extraParams: {
                    ckanUrl: defaultCkanUrl
                }
            }
        });

        // Top Toolbar
        myconfig.tbar = Ext4.create('Ext4.toolbar.Toolbar', {
            items: [
                {   // Refresh
                    scope: {obj: this, itemsPerPage: itemsPerPage},
                    handler: this._onRefreshClicked,
                    name: 'ckanreload',
                    cls: 'x-btn-icon',
                    tooltip: HS.i18n('Refresh'),
                    icon: HSRS.IMAGE_LOCATION + '/arrow_refresh.png'
                },
                {   // CKAN Switching
                    fieldLabel: HS.i18n("CKAN"),
                    xtype: 'combobox',
                    labelWidth: 40,
                    name: 'switchckan',
                    displayField: 'ckan',
                    valueField: 'ckan',
                    value: this.defaultCkanUrl,
                    store: Ext4.create('Ext4.data.Store', {
                        fields: ['ckan'],
                        data: [
                            {"ckan":"http://ckan-otn-dev.intrasoft-intl.com/"},
                            {"ckan":"http://www.civicdata.io/"},
                            {"ckan":"http://publicdata.eu/"}, 
                            {"ckan":"http://data.gov.uk"},
                            {"ckan":"http://data.gov.ro/"},
                            {"ckan":"http://data.gov.sk/"},
                            {"ckan":"http://data.gov.au/"},
                            {"ckan":"http://data.kk.dk/"},
                            {"ckan":"http://www.hri.fi/"},
                            {"ckan":"http://datamx.io/"} 
                        ]
                    }),
                    listeners: {
                        change: this._onCkanChanged,
                        scope: this
                    }                    
                }
            ]
        });

        // Bottom toolbar
        myconfig.bbar = Ext4.create('Ext4.toolbar.Toolbar', {
            items: [
                {   // Paging
                    xtype: 'pagingtoolbar',
                    store: myconfig.store,   // same store GridPanel is using
                    displayInfo: false
                }
            ]
        });

        myconfig.multiSelect = true;
        myconfig.autoScroll = true;
        myconfig.anchor = '100%';
        
        // Packages columns
        myconfig.columns = [
            {
                text: HS.i18n('Name'),
                sortable: true,
                flex: 1,
                dataIndex: 'name'
            },
            {
                text: HS.i18n('Format'),
                sortable: true,
                flex: 1,
                dataIndex: 'format'
            },
            {
                text: HS.i18n('Description'),
                sortable: true,
                flex: 1,
                dataIndex: 'description'
            }
        ];

/*
        // Datasets columns
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
*/

        // grouping according to organizations
        /* var groupingFeature = Ext4.create('Ext4.grid.feature.Grouping', {
            groupHeaderTpl: '{name}',
            hideGroupedHeader: true,
            collapsible: false
        }); */

        config = Ext4.Object.merge(myconfig, config);
        // config.features = [groupingFeature];

        this.callParent(arguments);
        this.addEvents('ckandownloaded');

        var makeMenu = function(view, record, elem, idx, e, opts) {

            // display ckan menu
            // var menu = Ext4.create('HSRS.LayerManager.CkanPanel.CkanDatasetMenu', {
            var menu = Ext4.create('HSRS.LayerManager.CkanPanel.CkanResourceMenu', {
                url: this.url,
                record: record,
                listeners: {
                    scope: this,
                    'copytofiles': this._onCopyToFiles
                    }
                });

            menu.showAt(e.xy[0], e.xy[1], elem);
            Ext4.EventManager.stopEvent(e);
        };

        this.on('itemcontextmenu', makeMenu, this);
        this.on('itemclick', makeMenu, this);

        myconfig.store.load({
            params:{
                start: 0,
                limit: itemsPerPage
            }
        });
    },

    _onCopyToFiles: function(urlToGet) {

        var filemanUrl = this.url.replace("ckan", "fileman");
        var url = filemanUrl + '?source=url&url=' + urlToGet;
        console.log(url);
        Ext4.Ajax.request({
            method: 'POST',
            url: (HSRS.ProxyHost ? HSRS.ProxyHost + escape(url) : url),
            success: function(form, action) {
                var obj;
                try {
                    obj = Ext4.decode(form.responseText);
                }
                catch (E) {
                    obj = {message: ''};
                }
                Ext4.Msg.alert(HS.i18n('Success'), HS.i18n('Resource copied to Files') +
                     '<br />' + obj.message);
                this.fireEvent('ckandownloaded'); // Fire event to LayerManager to refresh the Files
            },
            failure: function(form, action) {
                var obj;
                try {
                    obj = Ext4.decode(form.responseText);
                }
                catch (E) {
                    obj = {message: ''};
                }
                Ext4.Msg.alert(HS.i18n('Failed'), HS.i18n('Resource not copied into Files') +
                    '<br />' + obj.message);
            },
            scope: this
        });
    },

    _onCkanChanged: function(combo, newValue, oldValue, eOpts) {
        this.store.proxy.extraParams.ckanUrl = newValue;
        this.store.currentPage = 1;
        // this._onRefreshClicked();
        this.store.load({
            params:{
                start: 0,
                limit: this.itemsPerPage
            }
        });
    },

    /**
     * button refresh handler
     * @private
     */
     _onRefreshClicked: function() {
        this.obj.store.currentPage = 1;
        this.obj.store.load({
            params:{
                start: 0,
                limit: this.itemsPerPage
            }
        });
     }

});

