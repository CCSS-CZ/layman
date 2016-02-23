/*
    LayMan - the Layer Manager

    Copyright (C) 2016 Czech Centre for Science and Society
    Authors: Jachym Cepicky, Karel Charvat, Stepan Kafka, Michal Sredl, Premysl Vohnout
    Mailto: sredl@ccss.cz, charvat@ccss.cz

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

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
                    value: defaultCkanUrl,
                    store: Ext4.create('Ext4.data.Store', {
                        fields: ['ckan'],
                        data: [
                            {"ckan":"http://ckan-otn-dev.intrasoft-intl.com/"},
//                            {"ckan":"http://publicdata.eu/"}, 
                            {"ckan":"http://www.europeandataportal.eu/data/"},
                            {"ckan":"http://data.gov.uk"},
                            {"ckan":"http://data.gov.sk/"},
                            {"ckan":"http://data.kk.dk/"},
                            {"ckan":"http://www.hri.fi/"},
                            {"ckan":"http://data.gov.au/"},
                            {"ckan":"http://www.civicdata.io/"},
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

        var filemanUrl = this.url.replace("ckan", "files") + getLRUser();
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

