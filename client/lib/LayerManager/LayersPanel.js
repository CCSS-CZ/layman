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

Ext4.define('HSRS.LayerManager.LayersPanel', {

    extend: 'Ext4.grid.Panel',
    title: HS.i18n('Layers'),

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
                    tooltip: HS.i18n('Refresh'),
                    icon: HSRS.IMAGE_LOCATION + '/arrow_refresh.png'
                },
                /*{
                    scope: this,
                    handler: this._onDeleteClicked,
                    cls: 'x-btn-icon',
                    tooltip: 'Delete layer',
                    icon: HSRS.IMAGE_LOCATION + '/delete.png'
                }*/
                {   // Sync
                    scope: this,
                    handler: this._onSyncClicked,
                    text: HS.i18n('Sync'),
                    tooltip: HS.i18n('Synchronise with GeoServer')
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
                text: HS.i18n('Workspace'),
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
                dataIndex: 'type',
                align: 'center',
                //add in the custom tpl for the rows
                tpl: Ext4.create('Ext4.XTemplate', '{type:this.formatIcon}', {
                    formatIcon: function(v) {
                        return '<img src="' + HSRS.IMAGE_LOCATION + v.toLowerCase() + '-type.png" />';
                    }
                })
            },
            // layer column
            {
                text: HS.i18n('Layer'),
                // xtype: 'templatecolumn',
                sortable: true,
                flex: 1,
                dataIndex: 'layertitle'
            },
            // type 
            {
                text: 'Type',
                sortable: true,
                flex: 1,
                dataIndex: 'layertype'
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
                            Ext4.MessageBox.confirm(HS.i18n('Really remove selected layer?'),
                                    HS.i18n('Are you sure, you want to remove selected layer and the underlying data?')+ ' [' + record.get('layername') +'] <br />', 
                                    function(btn, x, msg) {
                                        if (btn == 'yes') {
                                            this.lm.deleteLayer(this.record.get('layername'),
                                                                this.record.get('workspace'),
                                                                this.record.get('layertitle'),
                                                                true); // deleteTable = true
                                        }
                                    },
                                    {lm: this, record: record});

                                },

                        'layeronlydeleted': function(record, evt) {
                            Ext4.MessageBox.confirm(HS.i18n('Really remove selected layer?'),
                                    HS.i18n('Are you sure, you want to remove selected layer?') + ' [' + record.get('layername') +'] <br />', 
                                    function(btn, x, msg) {
                                        if (btn == 'yes') {
                                            this.lm.deleteLayer(this.record.get('layername'),
                                                                    this.record.get('workspace'),
                                                                    this.record.get('layertitle'),
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
        var url = this.url;

        if (deleteTable == true) { // delete data as well
            url = url.replace('layers','datalayers');
        }

        // DELETE /layers/<group>/<layer> - delete layer only
        // DELETE /datalayers/<group>/<layer> - delete layer and data
        url = url + ws + '/' + layer; 

        title = title || layer;

        Ext4.MessageBox.show({
               msg: HS.i18n('Deleting layer') +' ['+title+'] ...',
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
                Ext4.Msg.alert(HS.i18n('Success'), HS.i18n('Deleting layer succeeded'));
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
    },

    _onSyncClicked: function() {
        var url = this.url.replace("layers", "sync/layers");

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
                Ext4.Msg.alert(HS.i18n('Success'), HS.i18n('Layers of all your groups has been synchronised') +
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
                Ext4.Msg.alert(HS.i18n('Failed'), HS.i18n('Synchronisation of layers failed') +
                    '<br />' + obj.message);
            }
        });
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
