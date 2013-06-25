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
                id: "publish_button",
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
            /* Workspace combo box
             * User has to define workspace first
             */
            {
                xtype: 'combobox',
                disabled: (config.isFeatureType ? true : false),
                name: 'usergroup',
                id: "usergroup",
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
                        /* Set default user group after store load
                         */
                        load: function(combo, records, ok, opts) {
                            if (this.val) {
                                this.form.getForm().setValues({"usergroup": this.val});
                            }
                        },
                        scope: {form: this, val: config.group}
                    },
                    fields: ['name', 'title']
                }),
                listeners: {
                    /* Enable other form fields, after user group/workspace
                     * selected
                     */
                    "change": function(combo, newValue, oldValue, eOpts){
                        if (!this.up().isFeatureType) {
                            this.up().down("#publish_as").enable();
                        }

                    }
                },
                editable: false,
                displayField: 'title',
                valueField: 'name'
            },

            /* Layer combobox
             * Either publish as new layer or update existing one
             */
            {
                xtype: 'combobox',
                disabled: (config.isFeatureType ? true : false),
                name: 'publish_as',
                id:"publish_as",
                anchor: '100%',
                fieldLabel: 'Publish as',
                store: Ext4.create('Ext4.data.JsonStore', {
                    autoLoad: true,
                    proxy: {
                        type: "ajax",
                        url: config.url,
                        model: 'HSRS.LayerManager.LayersPanel.Model',
                        reader: {
                            type: "json" 
                        }
                    },
                    listeners: {
                        /* Add "new layer" to the beginning of values
                         */
                        load: function(store, records, ok, opts) {
                            store.insert(0,[
                                Ext4.create("HSRS.LayerManager.LayersPanel.Model",{
                                    name:"newlayer",
                                    title:"New layer"
                                })
                            ]);
                        },
                        scope: {form: this, val: config.group}
                    }
                }),
                listeners: {
                    scope: this,
                    /* onvalue change -> existing layer is selected -> fill the
                     * form with already given values
                     */
                    "change": function(combo, newValue, oldValue, eOpts){
                        if (this._reseting) {
                            return;
                        }
                        this.up().down("#publishing_set").enable();
                        var ws = combo.up().down("#usergroup").getValue();
                        var find_record = function(record, id) {
                            if (record.get("workspace") == this.ws &&
                                record.get("layerData").name == this.val) {
                                return true;
                            }
                        };

                        // find record
                        var ridx = combo.store.findBy(find_record,
                                {ws:ws,val:newValue});

                        // record found, fill the form
                        if (ridx > -1) {
                            var record = combo.store.getAt(ridx);
                            this.layer = record.get("layer");
                            this.layerData = record.get("layerData");
                            this.getForm().setValues({
                                title: record.get("title"),
                                abstract: record.get("abstract"),
                                metadataurl: record.get("metadataurl"),
                                attribution_text: record.get("attribution_text"),
                                attribution_link: record.get("attribution_link"),
                                fileName: this.name,
                                layerName: newValue
                            });

                            this.isFeatureType = true;
                            this.down("#publish_button").setText("Update");
                            this.url = config.url+newValue;
                            this.down("#layerName").setValue(newValue);
                        }
                        // record not found -> new file to be published
                        else {
                            var vals = this.getForm().getValues();
                            this.layer = undefined;
                            this.layerData = undefined;
                            this._reseting = true;
                            this.getForm().reset();
                            this.getForm().setValues({
                                usergroup: vals.usergroup,
                                publish_as: vals.publish_as,
                                fileName: this.name,
                                layerName: newValue
                            });
                            this._reseting = false;

                            this.isFeatureType = false;
                            this.down("#publish_button").setText("Publish");
                            this.url = config.url;
                            this.down("#layerName").setValue(newValue);
                        }
                    }
                },
                editable: false,
                displayField: 'title',
                valueField: 'name'
            },            

            /* Metadata fieldset
             */
            {
                xtype: 'fieldset',
                disabled: (config.isFeatureType ? false : true),
                id: "publishing_set",
                title: config.isFeatureType ? "Edit layer settings" : "Publish file '" + config.name + "'",
                 items: [
                    
                     /* set name if this is existing feature type
                      */
                     {
                         name: "layerName",
                         id: "layerName",
                         xtype: 'hidden',
                         anchor: '100%',
                         value: (config.isFeatureType ? config.name : undefined)
                     },
                     /* set name of the file if this is file name
                      */
                     {
                         name: 'fileName',
                         id: 'fileName',
                         xtype: 'hidden',
                         disabled: (config.isFeatureType ? true : false),
                         anchor: '100%',
                         value: (config.isFeatureType ? undefined:config.name)
                     },
                    /* Title field
                     */
                     {
                         fieldLabel: 'Title',
                         xtype: 'textfield',
                         anchor: '100%',
                         name: 'title',
                         value: config.title
                     },
                    /* Abstract field
                     */
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

                    /* Metadata link field
                     */
                     {
                         fieldLabel: 'Metadata link',
                         anchor: '100%',
                         xtype: 'textfield',
                         name: 'metadataurl',
                         value: config.metadataurl || ''
                     },

                    /* CRS field
                     */
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

                    /* BBOX field set
                     */
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

                    /* Attribution field set
                     */
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

                Ext4.Ajax.request({
                    url: this.url, 
                    jsonData: {"featureType": {
                        title: vals.title,
                        abstract: vals.abstract
                        },
                        crs: vals.crs,
                        fileName: vals.fileName,
                        layer: this.layer
                    },
                    method: "PUT",
                    success: function(form,action) {
                            Ext4.MessageBox.hide();
                            this.fireEvent("updated", data);
                    },
                    failure: function(form, action) {
                        Ext4.MessageBox.hide();
                        var obj;
                        try {
                            obj = Ext4.decode(form.responseText);
                        }
                        catch(E){
                            obj = {message: ""};
                        }
                        Ext4.Msg.alert('Failed', 'Publishing file failed'+
                            "<br />"+ obj.message);
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
                        var obj;
                        try {
                            obj = Ext4.decode(action.response.responseText);
                        }
                        catch(E){
                            obj = {
                                message: ""
                            };
                        }
                        Ext4.Msg.alert('Failed', 'Publishing file failed'+
                            "<br />"+
                            obj.message);
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
