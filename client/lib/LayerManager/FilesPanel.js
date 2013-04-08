
Ext4.define('HSRS.LayerManager.FilesPanel', {

    requires: [
        'Ext4.data.JsonStore',
        'HSRS.LayerManager.FilesPanel.Model',
        'HSRS.LayerManager.FilesPanel.FileUploader',
        'HSRS.LayerManager.FilesPanel.FileMenu'
    ],

    extend: 'Ext4.grid.Panel',
    title: 'Files',
    url: '',
    groups: undefined,

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
                    handler: this._onUploadClicked,
                    cls: 'x-btn-icon',
                    tooltip: 'Upload new file',
                    icon: HSRS.IMAGE_LOCATION + '/add.png'
                },
                {
                    scope: this,
                    handler: this._onDeleteClicked,
                    cls: 'x-btn-icon',
                    tooltip: 'Delete file',
                    icon: HSRS.IMAGE_LOCATION + '/delete.png'
                }
            ]
        });

        myconfig.store = Ext4.create('Ext4.data.JsonStore', {
            model: 'HSRS.LayerManager.FilesPanel.Model',
            //autoLoad: true,
            //autoSync: true,
            proxy: {
                type: 'ajax',
                url: (HSRS.ProxyHost ? HSRS.ProxyHost + escape(config.url) : config.url),
                reader: {
                    type: 'json',
                    idProperty: 'name'
                }
            }
        });
        myconfig.store.load();

        myconfig.multiSelect = true;

        myconfig.autoScroll = true;
        myconfig.anchor = '100%';

        myconfig.columns = [
            // icon column
            //{
            //    xtype: 'templatecolumn',
            //    text: ' ',
            //    width: 22,
            //    flex: 0,
            //    sortable: true,
            //    dataIndex: 'type',
            //    align: 'center',
            //    //add in the custom tpl for the rows
            //    tpl: Ext4.create('Ext4.XTemplate', '{type:this.formatType}', {
            //        formatType: function(v) {

            //            return '<img src="'+HSRS.IMAGE_LOCATION+v+'-type.png" />';
            //        }
            //    })
            //},
            // filename column
            {
                text: 'Name',
                sortable: true,
                flex: 1,
                dataIndex: 'name'
            },
            // file type
            {
                xtype: 'templatecolumn',
                width: 100,
                text: 'Type',
                flex: 0,
                sortable: true,
                dataIndex: 'mimetype',
                tpl: Ext4.create('Ext4.XTemplate', '{mimetype:this.formatType}', {
                    formatType: function(v) {
                        var type = '';

                        switch (v) {
                            case 'application/x-zipped-shp':
                            case 'application/x-qgis':
                                type = 'ESRI Shapefile';
                                break;
                        }
                        return type;

                    }
                })
            },
            // file size
            {
                xtype: 'templatecolumn',
                text: 'Size',
                sortable: true,
                flex: 0,
                width: 75,
                dataIndex: 'size',
                tpl: Ext4.create('Ext4.XTemplate', '{size:this.formatSize}', {
                    formatSize: function(filesize) {
                        return HSRS.formatSize(filesize);
                    }
                })
            },
            // date
            {
                xtype: 'templatecolumn',
                text: 'Date',
                sortable: true,
                flex: 0,
                width: 100,
                dataIndex: 'date',
                tpl: Ext4.create('Ext4.XTemplate', '{date:this.formatDate}', {
                    formatDate: function(v) {
                        return String(v);
                    }
                })
            }
        ];

        config = Ext4.Object.merge(myconfig, config);
        this.callParent([config]);
        this.addEvents('filepublished');

        var makeMenu = function(view, record, elem, idx, e, opts) {
            this.getFileDetail(record.get('name'), function(r) {

                // display file menu
                var menu = Ext4.create('HSRS.LayerManager.FilesPanel.FileMenu', {
                    url: this.url,
                    data: Ext4.JSON.decode(r.responseText),
                    groups: this.groups,
                    record: record,
                    listeners: {
                        scope: this,
                        'filepublished': this._onFilePublished,

                        // file deleted listener will popup confirmation window
                        'filedeleted': function(record, evt) {
                            Ext4.MessageBox.confirm('Really remove selected file?',
                                    'Are you sure, you want to remove selected file? <br />'+
                                    record.get('name'),
                                    function(btn, x, msg) {
                                        if (btn == 'yes') {
                                            this.fm.deleteFile(this.record.get('name'));
                                        }
                                    },
                                    {fm: this, record: record});

                                }
                    }
            });

            menu.showAt(e.xy[0], e.xy[1], elem);
            }, this);
            Ext4.EventManager.stopEvent(e);
        };

        this.on('itemcontextmenu', makeMenu, this);
        this.on('itemclick', makeMenu, this);
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
        var url = this.url.replace(/\/$/, '') + '/detail/'+ name;
        Ext4.Ajax.request({
            url: (HSRS.ProxyHost ? HSRS.ProxyHost + escape(url) : url),
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
        var fileUploader = Ext4.create('HSRS.LayerManager.FilesPanel.FileUploader', {
            filesnames: this.store.collect('name'),
            url: this.url,
            listeners: {
                scope: fileUploader,
                'filesaved': function() {
                    this._win.close();
                }
            }
        });

        fileUploader.on('filesaved', function() {
            this.store.load();
        },this);

        fileUploader._win = Ext4.create('Ext4.window.Window', {
            title: 'File upload',
            height: 150,
            width: 400,
            layout: 'fit',
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
            Ext4.MessageBox.confirm('Really remove selected files?',
                    'Are you sure, you want to remove selected files? <br />'+
                    records.map(function(r) {return r.get('name');}).join('<br />'),
                    function(btn, x, msg) {
                        if (btn == 'yes') {
                            for (var i = 0, ilen = this.records.length; i < ilen; i++) {
                                this.fm.deleteFile(this.records[i].get('name'));
                            }
                        }
                        /*this.deleteFile;*/
                    },
                    {fm: this, records: records});
        }
    },

    /**
     * send delete request
     *
     * @function
     * @param file {String}  file name.
     */
    deleteFile: function(file) {
        var url = this.url + file;
        console.log(this.url);
        Ext4.Ajax.request({
            method: 'DELETE',
            url: (HSRS.ProxyHost ? HSRS.ProxyHost + escape(url) : url),
            success: function() {
                console.log('####', arguments);
            },
            scope: this
        });
        this.store.load();
    },

    /**
     * set list of groups
     *
     */
    setGroups: function(groups) {
        this.groups = groups;
    },

    /**
     * file published handler
     * @private
     * @function
     */
    _onFilePublished: function(data) {
        this.fireEvent('filepublished', data);
    }
});
