/**
 * License: ...
 * @author: Jachym
 */

Ext4.define('HSRS.LayerManager.PublishForm', {

    extend: 'Ext4.form.Panel',
    groups: undefined,
    isFeatureType: false,
    featureType: undefined,
    layer: undefined,

    /**
     * @constructor
     */
    constructor: function(config) {
        config.items = this._initItems(config);
        config.layout = 'anchor';
        config.frame = true;
        config.url = config.isFeatureType ? config.url+config.name : config.url;
        config.buttons = [
            {
                text: config.isFeatureType ? "Update" : 'Publish',
                scope: this,
                handler: this._onPublishClicked
            },
            {
                text: 'Reset',
                scope: this,
                handler: this._onResetClicked
            },
            {
                text: 'Cancel',
                scope: this,
                handler: this._onCancelClicked
            }
        ];

        config.title = undefined;

        this.callParent(arguments);


        this.addEvents('published', "updated",'canceled', 'reset');
    },

    /**
     * @function
     * @private
     */
    _initItems: function(config) {


        Ext4.define('HSRS.LayerManager.PublishForm.GroupModel', {
            extend:"Ext4.data.Model",
            fields: [{
                name: "name",
                mapping: "roleName"
            },
            {
                name: "title",
                mapping: "roleTitle"
            }]
        });

        var items = [
            {
                xtype: 'fieldset',
                title: config.isFeatureType ? "Edit layer settings" : "Publish file '" + config.name + "'",
                items: [
                    {
                        xtype: 'combobox',
                        name: 'usergroup',
                        anchor: '100%',
                        fieldLabel: 'Group',
                        store: Ext4.create('Ext4.data.JsonStore', {
                            autoLoad: true,
                            proxy: {
                                type: "ajax",
                                url: config.url+"groups",
                                model: 'HSRS.LayerManager.PublishForm.GroupModel',
                                reader: {
                                    type: "json",
                                    idProperty: "name"
                                }
                            },
                            listeners: {
                                load: function(combo, records, ok, opts) {
                                    if (this.val) {
                                        this.form.getForm().setValues({"usergroup": this.val});
                                    }
                                },
                                scope: {form: this, val: config.group}
                            },
                            fields: ['name', 'title']
                        }),
                        editable: false,
                        displayField: 'title',
                        valueField: 'name'
                    },
                    {
                        xtype: 'combobox',
                        name: 'newlayer',
                        anchor: '100%',
                        fieldLabel: 'Publish as',
                        value: "new layer",
                        store: Ext4.create('Ext4.data.JsonStore', {
                            autoLoad: true,
                            proxy: {
                                type: "ajax",
                                url: config.url+"groups",
                                model: 'HSRS.LayerManager.PublishForm.GroupModel',
                                reader: {
                                    type: "json",
                                    idProperty: "name"
                                }
                            },
                            listeners: {
                                load: function(combo, records, ok, opts) {
                                    if (this.val) {
                                        this.form.getForm().setValues({"newlayer": this.val});
                                    }
                                },
                                scope: {form: this, val: config.group}
                            },
                            fields: ['name', 'title']
                        }),
                        editable: false,
                        displayField: 'title',
                        valueField: 'name'
                    },
                    {
                        name: config.isFeatureType ? "layerName" : 'fileName',
                        xtype: 'hidden',
                        anchor: '100%',
                        value: config.name
                    },
                    {
                        fieldLabel: 'Title',
                        xtype: 'textfield',
                        anchor: '100%',
                        name: 'title',
                        value: config.title
                    },
                    {
                        fieldLabel: 'Abstract',
                        xtype: 'textarea',
                        anchor: '100%',
                        name: 'abstract',
                        value: config.abstract || config.description || ''
                    },
                    //{
                    //    fieldLabel: 'Keywords',
                    //    xtype: 'multiselect',
                    //    anchor: '100%',
                    //    msgTarget: 'side',
                    //    name: 'keywords',
                    //    allowBlank: true,
                    //    store: {
                    //        fields: [ 'keyword' ],
                    //        data: [["keyword1"]]
                    //    },
                    //    valueField: 'keyword',
                    //    displayField: 'keyword'
                    //},
                    {
                        fieldLabel: 'Metadata link',
                        anchor: '100%',
                        xtype: 'textfield',
                        name: 'metadataurl',
                        value: config.metadataurl || ''
                    },
                    {
                        title: 'Coordinate Reference Systems',
                        anchor: '100%',
                        xtype: 'fieldset',
                        layout: 'anchor',
                        items: [
                            {
                                fieldLabel: 'Native SRS',
                                anchor: '100%',
                                xtype: 'textfield',
                                value: config.prj || '',
                                name: 'crs'
                            }
                        ]
                    },
                    {
                        title: 'Bounding Box',
                        xtype: 'fieldset',
                        anchor: '100%',
                        items: [
                            {
                                fieldLabel: 'Bounds',
                                hideLabel: true,
                                xtype: 'fieldcontainer',
                                name: 'bbox',
                                anchor: '100%',
                                layout: {
                                    type: 'table',
                                    columns: 3
                                },
                                defaults: {
                                    xtype: 'container',
                                    width: 75
                                },
                                items: [
                                    { html: ' ' },
                                    {
                                        name: 'maxy',
                                        xtype: 'textfield',
                                        value: (config.extent ? config.extent[3] : '')
                                    },
                                    { html: ' ' },
                                    {
                                        name: 'minx',
                                        xtype: 'textfield',
                                        value: (config.extent ? config.extent[0] : '')
                                    },
                                    { html: ' ' },
                                    {
                                        name: 'maxx',
                                        xtype: 'textfield',
                                        value: (config.extent ? config.extent[2] : '')
                                    },
                                    { html: ' ' },
                                    {
                                        name: 'miny',
                                        xtype: 'textfield',
                                        value: (config.extent ? config.extent[1] : '')
                                    },
                                    { html: ' ' }
                                ]
                            }
                        ]
                    },
                    {
                        title: 'Attribution',
                        anchor: '100%',
                        xtype: 'fieldset',
                        layout: 'anchor',
                        items: [
                            {
                                fieldLabel: 'Attribution text',
                                anchor: '100%',
                                xtype: 'textfield',
                                value: config.attribution ? config.attribution.text : '',
                                name: 'attribution_text'
                            },
                            {
                                fieldLabel: 'Attribution link',
                                anchor: '100%',
                                xtype: 'textfield',
                                emptyText: 'http://',
                                value: config.attribution ? config.attribution.link : '',
                                name: 'attribution_link'
                            }
                        ]
                    }
                ]
            }
        ];

        return items;
    },

    /*
     * @private
     */
    _onPublishClicked: function() {
        var form = this.getForm();
        var data = form.getValues();

        if (form.isValid()) {
            // submit FeatureTypes using http PUT
            Ext4.MessageBox.show({
                   msg: 'Importing data to database, creating new layer ...',
                   progressText: 'Importing file ...',
                   width:300,
                   wait:true,
                   waitConfig: {interval:200},
                   icon: 'ext4-mb-download', //custom class in msg-box.html
                   iconHeight: 50
               });

            if (this.isFeatureType) {
                var vals = form.getValues();
                //this.featureType.abstract = vals.abstract;
                //this.featureType.title = vals.title;

                Ext4.Ajax.request({
                    url: this.url, 
                    jsonData: {"featureType": {
                        title: vals.title,
                        abstract: vals.abstract
                        },
                        layer: this.layer
                    },
                    method: "PUT",
                    success: function(form,action) {
                            Ext4.MessageBox.hide();
                            this.fireEvent("updated", data);
                    },
                    failure: function(form, action) {
                        Ext4.MessageBox.hide();
                        Ext4.Msg.alert('Failed', 'Publishing file failed');
                    },
                    scope: this
                });
            }
            // submit new files using http POST
            else {
                form.submit({
                    success: function(form,action) {
                            Ext4.MessageBox.hide();
                            this.fireEvent('published', data);
                    },
                    failure: function(form, action) {
                        Ext4.MessageBox.hide();
                        Ext4.Msg.alert('Failed', 'Publishing file failed');
                    },
                    scope: this
                });
            }
        }

    },
    /*
     * @private
     */
    _onResetClicked: function() {
        this.fireEvent('reset');
        this.getForm().reset();
    },

    /*
     * @private
     */
    _onCancelClicked: function() {
        this.fireEvent('canceled');
    }
});
