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

/* Fill the Metadata Link field 
 * Callback function for Micka
 */
window.fillMetadataLinkFromMicka = function(uuid) {
    document.getElementById("MetadataLink-inputEl").value = uuid;
}

Ext4.define('HSRS.LayerManager.PublishForm', {

    requires: ['HSRS.LayerManager.PublishForm.LayersCombo',
               'HSRS.LayerManager.PublishForm.ItemSelector'],
    extend: 'Ext4.form.Panel',
    groups: undefined,
    type: undefined, // "file", "data" or "layer"
    featureType: undefined,
    layer: undefined,
    _url: undefined,

    /**
     * @constructor
     */
    constructor: function(config) {
        config.items = this._initItems(config);
        config.layout = 'anchor';
        config.width = 500;
        config.frame = true;
        config.timeout = 120;
        config.url = config.type == "layer" ? config.url + config.name :
                     config.url;
        this._url = config.url;
        config.buttons = [
            {
                text: config.type == "layer" ? HS.i18n('Update') : HS.i18n('Publish'),
                id: 'publish_button',
                scope: this,
                handler: this._onPublishClicked
            },
            {
                text: HS.i18n('Reset'),
                scope: this,
                handler: this._onResetClicked
            },
            {
                text: HS.i18n('Cancel'),
                scope: this,
                handler: this._onCancelClicked
            }
        ];

        config.title = undefined;

        this.callParent(arguments);

        this.addEvents('published', 'updated', 'canceled', 'reset');
    },

    /**
     * @private
     */
    _initItems: function(config) {


        Ext4.define('HSRS.LayerManager.PublishForm.GroupModel', {
            extend: 'Ext4.data.Model',
            fields: [{
                name: 'name',
                mapping: 'roleName'
            },
            {
                name: 'title',
                mapping: 'roleTitle'
            }]
        });

        Ext4.define('HSRS.LayerManager.PublishForm.AllGroupModel', {
            extend: 'Ext4.data.Model',
            fields: [{
                name: 'name',
                mapping: 'roleName'
            },
            {
                name: 'title',
                mapping: 'roleTitle'
            }]
        });
        var items = [
            /* Workspace combo box
             * User has to define workspace first
             */
            {
                xtype: 'combobox',
                disabled: config.type == "file" ? false : true,
                name: 'usergroup',
                id: 'usergroup',
                anchor: '100%',
                fieldLabel: HS.i18n('Publish to'),
                store: Ext4.create('Ext4.data.JsonStore', { // FIXME - this should be done ONCE, not everytime the Publish/Update is clicked
                    autoLoad: true,
                    proxy: {
                        type: 'ajax',
                        url: config.url.replace('datalayers','groups/mine'), // Here we get the groups of the user
                        model: 'HSRS.LayerManager.PublishForm.GroupModel',
                        reader: {
                            type: 'json',
                            idProperty: 'name'
                        }
                    },
                    listeners: { 
                        /* Set default user group after store load
                         */
                        load: function(combo, records, ok, opts) {
                            if (this.val) {
                                this.form.getForm().setValues({
                                    'usergroup': this.val
                                });
                            }
                            /*var read_groups = this.form.down('#read_groups');
                            read_groups.fromField.store.removeAll();
                            read_groups.toField.store.removeAll();
                            for (var i = 0, ilen = records.length;
                                 i < ilen;
                                 i++) {
                                this.form.down(
                                    '#read_groups').fromField.store.loadData(
                                    [records[i].copy()],
                                    true);
                            }*/
                        },
                        scope: {form: this, val: config.group}
                    }, 
                    fields: ['name', 'title']
                }),
                listeners: {
                    /* Enable other form fields, after user group/workspace
                     * selected
                     */
                    'change': function(combo, newValue, oldValue, eOpts) {
                        if (this.up().type == "file") {
                            var publish_as = this.up().down('#publish_as');
                            publish_as.enable();
                            publish_as.loadLayers(newValue);
                            if (publish_as.getValue()) {
                                this.up().down('#publishing_set').enable();
                            }

                            // mark selected group for read automatically
                            var read_groups = this.up().down('#read_groups');
                            //read_groups.toField.store.removeAll();
                            var i = combo.store.find('name', newValue);

                            var sm = read_groups.fromField.boundList.getSelectionModel();
                            sm.select(combo.store.getAt(i));
                            read_groups.onAddBtnClick();
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
                xtype: 'layerscombo',
                name: 'publish_as',
                url: config.url,
                id: 'publish_as',
                disabled: (config.type == "layer" ? true : true),
                anchor: '100%',
                fieldLabel: HS.i18n('Publish as'),
                value: 'newlayer',
                listeners: {
                    change: this._onLayerChangeHandler,
                    scope: this
                }
            },

            /* Metadata fieldset
             */
            {
                xtype: 'tabpanel',
                deferredRender:false,
                id: 'publishing_set',
                disabled: (config.type == "file" ? true : false),
                plain: true,
                activeTab: 0,
                defaults: {
                    bodyPadding: 10,
                    frame: true
                },
                items: [{
                    title: 'Basic',
                    items: [{
                        xtype: 'fieldset',
                        //disabled: (config.isFeatureType ? false : true),
                        //id: 'publishing_set',
                        title: HS.i18n('Metadata of') + ' "' + config.name + '"',
                        layout: 'anchor',
                         items: [
                           /* set name if this is layer
                            */
                           {
                               name: 'layerName',
                               id: 'layerName',
                               xtype: 'hidden',
                               anchor: '100%',
                               value: (config.type == "layer" ?
                                       config.name : undefined)
                           },
                           /* set name of the file if this is file 
                            */
                           {
                               name: 'fileName',
                               id: 'fileName',
                               xtype: 'hidden',
                               disabled: (config.type == "file" ?
                                          false : true),
                               anchor: '100%',
                               value: (config.type == "file" ?
                                       config.name : undefined)
                           },
                           /* set table/view name if this is data
                            */
                           {
                               name: 'view',
                               id: 'viewName',
                               xtype: 'hidden',
                               disabled: (config.type == "data" ?
                                          false : true),
                               anchor: '100%',
                               value: (config.type == "data" ?
                                       config.name : undefined)
                           },
                           /* set datatype if this is data
                            */
                           {
                               name: 'datatype',
                               id: 'datatype',
                               xtype: 'hidden',
                               disabled: (config.type == "data" ?
                                          false : true),
                               anchor: '100%',
                               value: (config.type == "data" ?
                                       config.datatype : undefined)
                           },
                           /* set schema name if this is data
                            */
                           {
                               name: 'schema',
                               id: 'schemaName',
                               xtype: 'hidden',
                               disabled: (config.type == "data" ?
                                          false : true),
                               anchor: '100%',
                               value: (config.type == "data" ?
                                       config.group : undefined)
                           },
                          /* Title field
                           */
                           {
                               fieldLabel: HS.i18n('Title'),
                               xtype: 'textfield',
                               anchor: '100%',
                               name: 'title',
                               value: config.title,
                               validator: function(val) {
                                    v = val.trim()
                                    if (v=="") {
                                        return "Please fill in the title";
                                    } else {
                                        return true;
                                    }
                               }
                           },
                          /* Abstract field
                           */
                           {
                               fieldLabel: HS.i18n('Abstract'),
                               xtype: 'textarea',
                               anchor: '100%',
                               name: 'abstract',
                               value: config.abstract ||
                                   config.description || ''
                           },
                          /* Keywords field
                           */
                           {
                               fieldLabel: HS.i18n('Keywords'),
                               xtype: 'textfield',
                               anchor: '100%',
                               name: 'keywords',
                               value: config.keywords,
                               id: 'keywords',
                               allowBlank: true
                           },
                         {
                             title: HS.i18n('Metadata link'),
                             anchor: '100%',
                             xtype: 'fieldset',
                             layout: 'anchor',
                             rtl: true,
                             items: [
                          /* Metadata link field
                           */
                               {
                                   //fieldLabel: 'Metadata link',
                                   itemId: 'MetadataLink',
                                   id: 'MetadataLink',
                                   //emptyText: 'http://',
                                   anchor: '100%',
                                   xtype: 'textfield',
                                   name: 'metadataurl',
                                   value: config.metadataurl || ''
                               },
                               /* Selec existing Micka record
                                */
                               {
                                    text: HS.i18n('Select existing'),
                                    xtype: 'button',
                                    rtl: true,
                                    listeners: {
                                        click: function() {
                                            uuid = ""
                                            
                                            // Get current link - if any
                                            metadatalinkTextField = Ext4.getCmp('MetadataLink');
                                            currentLink = metadatalinkTextField.value; // http://erra.ccss.cz/php/metadata/?ak=xml&uuid=5153f659-17bc-45be-a09e-357f585671ec
                                            // Parse out uuid
                                            if (currentLink) {
                                                params = HSRS.getUrlParams(currentLink);
                                                if ("uuid" in params) {
                                                    uuid = params["uuid"];                                                
                                                }
                                            }

                                            // Open Micka
                                            mickaUrl = uuid == "" ?
                                                "/php/metadata/?cb=opener.fillMetadataLinkFromMicka" :
                                                "/php/metadata/?request=GetRecords&format=text/html&query=identifier=" + uuid + "&cb=opener.fillMetadataLinkFromMicka"
                                            window.open(mickaUrl, '_newtab');
                                        }
                                    },
                                    scope: this                                
                               },
                               /* Create new Micka record
                                */
                               {
                                    text: HS.i18n('Create new metadata record'),
                                    xtype: 'button',
                                    rtl: true,
                                    listeners: {
                                        click: function() {
                                            mickaUrl = "/php/metadata/index.php?request=GetRecords&format=text/html&language=&ak=new&cb=opener.fillMetadataLinkFromMicka"
                                            window.open(mickaUrl, '_newtab');
                                        }
                                    },
                                    scope: this                                
                               }
                            ]
                         }
                        ]
                    },
                  /* Attribution field set
                   */
                   {
                       title: HS.i18n('Attribution'),
                       anchor: '100%',
                       xtype: 'fieldset',
                       layout: 'anchor',
                       items: [
                           {
                               fieldLabel: HS.i18n('Attribution text'),
                               anchor: '100%',
                               xtype: 'textfield',
                               value: config.attribution_text ?
                                      config.attribution_text : '',
                               name: 'attribution_text'
                           },
                           {
                               fieldLabel: HS.i18n('Attribution link'),
                               anchor: '100%',
                               xtype: 'textfield',
                               emptyText: 'http://',
                               value: config.attribution_link ?
                                      config.attribution_link : '',
                               name: 'attribution_link'
                           }
                       ]
                   }
               ]
            },
                {
                    title: HS.i18n('Advanced'),
                    items: [
                        /* Read access
                         */
                        {
                            xtype: 'fieldset',
                            anchor: '100%',
                            layout: 'anchor',
                            title: HS.i18n('Read access'),
                            items: [ 
                              {
                                xtype: 'checkbox',
                                boxLabel: HS.i18n('Secure layer'),
                                name: 'secureLayer',
                                id: 'secureLayer',
                                checked: 'secureLayer' in config ?
                                         config.secureLayer : true,
                                inputValue: true,
                                uncheckedValue: false,
                                handler: function(field, value) {
                                    if (value) {
                                       Ext4.getCmp('read_groups').enable();         
                                    }
                                    else {
                                       Ext4.getCmp('read_groups').disable();         
                                    }
                                }
                              },
                              {
                                xtype: 'itemselector',
                                name: 'read_groups',
                                id: 'read_groups',
                                disabled: 'secureLayer' in config ?
                                          !config.secureLayer : false,
                                anchor: '100%',
                                //width: '100%',
                                //fieldLabel: 'Enable read',
                                buttons: ['add', 'remove'],
                                height: 100,
                                store: Ext4.create('Ext4.data.JsonStore', { // FIXME - this should be done ONCE - not for every layer everytime a button is clicked
                                    autoLoad: true,
                                    // model: 'HSRS.LayerManager.PublishForm.GroupModel'
                                    proxy: {
                                        type: 'ajax',
                                        url: config.url.replace('datalayers','groups/all'), // Here we get all the groups
                                        model: 'HSRS.LayerManager.PublishForm.AllGroupModel',
                                        reader: {
                                            type: 'json',
                                            idProperty: 'name'
                                        }
                                    },
                                    fields: ['name', 'title']
                                }),
                                displayField: 'title',
                                valueField: 'name',
                                allowBlank: true, // Shoudl this be rather false?
                                msgTarget: 'side',
                                fromTitle: HS.i18n('Deny'),
                                toTitle: HS.i18n('Allow')
                              }
                            ]
                        },
                        /* CRS field
                         */
                         {
                             title: HS.i18n('Data specification'),
                             anchor: '100%',
                             xtype: 'fieldset',
                             layout: 'anchor',
                             items: [
                                 {
                                     fieldLabel: HS.i18n('Native SRS'),
                                     anchor: '100%',
                                     xtype: 'combobox',
                                     emptyText: "EPSG:",
                                     value: (config.prj == "None:None" || config.prj == '' ? "" : config.prj),
                                     validator: function(val) {
                                        msg = "Please specify the SRS, e.g 'EPSG:4326'";
                                        var a = val.split(":");
                                        if (a.length == 2) {
                                            a[0] = a[0].trim().toLowerCase(); 
                                            a[1] = a[1].trim();
                                            if ( (a[0] == "epsg") && !isNaN(parseInt(a[1])) && isFinite(a[1]) ) {
                                                return true;
                                            }
                                        }
                                        return msg;
                                     },
                                     name: 'crs',
                                     editable: true,
                                     displayField: 'name',
                                     valueField: 'code',
                                     store: Ext4.create('Ext4.data.Store', {
                                        fields: ['code', 'name'],
                                        data : [
                                            {"code":"EPSG:3857", "name":"EPSG:3857"},
                                            {"code":"EPSG:4326", "name":"EPSG:4326"}
                                        ]
                                    })
                                 },
                                 {
                                     xtype: 'hidden',
                                     name: 'tsrs',
                                     value: config.tsrs
                                 },
                                {
                                    fieldLabel: HS.i18n('Code page'),
                                    anchor: '100%',
                                    xtype: 'combobox',
                                    name: 'cpg',
                                    disabled: config.type == "file" ? false : true,
                                    displayField: 'name',
                                    valueField: 'code',
                                    editable: true,
                                    store: Ext4.create('Ext4.data.Store', {
                                        fields: ['code', 'name'],
                                        data : [
                                            {"code":"UTF-8", "name":"UTF-8"},
                                            {"code":"1250", "name":"1250 - Central and Eeaster European Latin"},
                                            {"code":"1251", "name":"1251 - Cyrillic"},
                                            {"code":"1252", "name":"1252 - West European Latin"},
                                            {"code":"1253", "name":"1253 - Greek"},
                                            {"code":"1254", "name":"1254 - Turkish"},
                                            {"code":"1257", "name":"1257 - Baltic"},
                                        ]
                                    })
                                }
                             ]
                         },
                        /* BBOX field set
                         */
                         {
                             title: HS.i18n('Bounding Box'),
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
                                         xtype: 'container'
                                         //width: 75
                                     },
                                     items: [
                                         { html: ' ' },
                                         {
                                             name: 'maxy',
                                             xtype: 'textfield',
                                             value: (config.extent ?
                                                     config.extent[3] : '')
                                         },
                                         { html: ' ' },
                                         {
                                             name: 'minx',
                                             xtype: 'textfield',
                                             value: (config.extent ?
                                                     config.extent[0] : '')
                                         },
                                         { html: ' ' },
                                         {
                                             name: 'maxx',
                                             xtype: 'textfield',
                                             value: (config.extent ?
                                                     config.extent[2] : '')
                                         },
                                         { html: ' ' },
                                         {
                                             name: 'miny',
                                             xtype: 'textfield',
                                             value: (config.extent ?
                                                     config.extent[1] : '')
                                         },
                                         { html: ' ' }
                                     ]
                                 }
                             ]
                         }
                    ],
                    listeners: {
                        activate: function(panel, opts) {

                                            if (config.type == "layer") { // If the layer is already published

                                                // Go through the provided list, 
                                                // select from Available groups,
                                                // and click the Add button 
                                                grantList = config.readGroups;
                                                var read_groups = Ext4.getCmp('read_groups');
                                                var sm = read_groups.fromField.boundList.getSelectionModel();
                                                for (var i=0, len=grantList.length; i<len; ++i) {
                                                    // Click the "Add" button       
                                                    // var read_groups = this.form.down('#read_groups');
                                                    sm.select(grantList[i]);
                                                    read_groups.onAddBtnClick();
                                                }
                                            }  
                        },
                        scope: this
                    }
                }]
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
            Ext4.MessageBox.show({
                   msg: HS.i18n('Publishing ...'),
                   progressText: HS.i18n('Publishing ...'),
                   width: 300,
                   wait: true,
                   waitConfig: {interval: 200},
                   icon: 'ext4-mb-download', //custom class in msg-box.html
                   iconHeight: 50
               });
            
            if (this.type == "layer") { // Layer panel

                // Update Layer Settings 

                // Sent back what we previously received from GeoServer through LayMan server GET Layers
                // Set the values that were shown/edited in the GUI
                var vals        = form.getValues();
                newLayerData    = this.layerData;   // "featureType" or "coverage" json of geoserver
                newLayer        = this.layer;       // "layer" json of geoserver

                // Layer data params
    
                // Title, Abstract, SRS
                newLayerData.title      = vals.title;
                newLayerData.abstract   = vals.abstract;
                newLayerData.srs        = vals.crs;

                // Bounding Box
                if (!newLayerData.latLonBoundingBox) {
                    newLayerData.latLonBoundingBox = {};
                }
                newLayerData.latLonBoundingBox.minx = vals.minx;
                newLayerData.latLonBoundingBox.miny = vals.miny;
                newLayerData.latLonBoundingBox.maxx = vals.maxx;
                newLayerData.latLonBoundingBox.maxy = vals.maxy;

                // Keywords
                if (!newLayerData.keywords) {
                    newLayerData.keywords = {}
                }
                newLayerData.keywords.string = vals.keywords;

                // Metadata
                if (vals.metadataurl.trim() != "") { // Link provided
                    if (!newLayerData.metadataLinks) {
                        newLayerData.metadataLinks = {}
                    }
                    if (!newLayerData.metadataLinks.metadataLink) {
                        newLayerData.metadataLinks.metadataLink = []
                    }
                    if (!newLayerData.metadataLinks.metadataLink[0]) {
                        newLayerData.metadataLinks.metadataLink[0] = {}
                    }
                    newLayerData.metadataLinks.metadataLink[0].content =  vals.metadataurl;
                    newLayerData.metadataLinks.metadataLink[0].type = "text/xml";
                    newLayerData.metadataLinks.metadataLink[0].metadataType = "ISO19115:2003";                   

                } else { // Link not given
                    if (newLayerData.metadataLinks) { // something was there
                        // erase the list
                        newLayerData.metadataLinks = {} // this is nasty - GeoServer handles more than one metadata link
                    }
                    // else - nothing was there and link not given - nothing to do
                }

                // Layer params

                // Attribution
                if (!newLayer.attribution) {
                    newLayer.attribution = {}
                }
                newLayer.attribution.title = vals.attribution_text;
                newLayer.attribution.href  = vals.attribution_link;

                // Access Control

                // Secure Layer
                newSecureLayer = vals.secureLayer;

                // Read groups
                newReadGroups = vals.read_groups;


                // PUT Layer Config 

                Ext4.Ajax.request({
                    url: this.url,
                    jsonData: {
                        usergroup:   this.group,     // group=workspace
                        fileName:    vals.fileName,  // wtf?
                        layer:       newLayer,       // "layer" json of geoserver
                        layerData:   newLayerData,   // "featureType" or "coverage" json of geoserver
                        secureLayer: newSecureLayer, // If the layer should be secured
                        readGroups:  newReadGroups   // Groups that should have the Read Access
                    },
                    method: 'PUT',
                    success: function(form, action) {
                            Ext4.MessageBox.hide();
                            this.fireEvent('updated', data);
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
                        Ext4.Msg.alert(HS.i18n('Failed'), HS.i18n('Settings update failed') +
                            '<br />' + obj.message);
                    },
                    scope: this
                });
            }

            // submit new files using http POST
            else if (this.type == "file") { // File Panel
                form.url = this._url + data.usergroup; // POST /datalayers/<group>
                form.submit({
                    success: function(form, action) {
                            Ext4.MessageBox.hide();
                            this.fireEvent('published', data);
                    },
                    failure: function(form, action) {
                        Ext4.MessageBox.hide();
                        var obj;
                        try {
                            obj = Ext4.decode(action.response.responseText);
                        }
                        catch (E) {
                            obj = {
                                message: ''
                            };
                        }
                        Ext4.Msg.alert(HS.i18n('Failed'), HS.i18n('Publishing failed') +
                            '<br />' + obj.message);
                    },
                    scope: this
                });
            }

            else if (this.type == "data") { // Data Panel
                form.url = this._url + this.group; // POST /layers/<group>
                form.submit({
                    success: function(form, action) {
                            Ext4.MessageBox.hide();
                            this.fireEvent('published', data);
                    },
                    failure: function(form, action) {
                        Ext4.MessageBox.hide();
                        var obj;
                        try {
                            obj = Ext4.decode(action.response.responseText);
                        }
                        catch (E) {
                            obj = {
                                message: ''
                            };
                        }
                        Ext4.Msg.alert(HS.i18n('Failed'), obj.message);
                    },
                    scope: this
                });
            }
        } else {
            Ext4.Msg.alert('Some fields are invalid', 'Please correct the invalid fields. (Title and EPSG code must be given)');
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
    },

    /**
     * layer change handler
     */
    _onLayerChangeHandler: function(combo, newValue, oldValue, eOpts) {
        if (this._reseting) {
            return;
        }
        this.down('#publishing_set').enable();
        var ws = combo.up().down('#usergroup').getValue();
        var find_record = function(record, id) {
            if (record.get('workspace') == this.ws &&
                record.get('layerData').name == this.val) {
                return true;
            }
        };

        // find record
        var ridx = combo.store.findBy(find_record,
                {ws: ws, val: newValue});

        // record found, fill the form
        if (ridx > -1) {
            var record = combo.store.getAt(ridx);
            this.layer = record.get('layer');
            this.layerData = record.get('layerData');
            this.readGroups = record.get('readGroups');
            this.secureLayer = record.get('secureLayer');
            var metadataurl = '';
            if (this.layerData.metadataLinks) {
                metadataurl = this.layerData.metadataLinks.metadataLink[0].content;
            }
            this.getForm().setValues({
                title: record.get('title'),
                abstract: this.layerData.abstract,
                keywords: this.layerData.keywords.string.join(','),
                metadataurl: metadataurl,
                attribution_text: this.layer.attribution.title,
                attribution_link: this.layer.attribution.href,
                fileName: this.name,
                layerName: newValue
            });

            this.type = "layer";
            this.down('#publish_button').setText('Update');
            this.url = this._url + newValue;
            this.down('#layerName').setValue(newValue);
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

            this.down('#publish_button').setText(HS.i18n('Publish'));
            this.url = this._url;
            this.down('#layerName').setValue(newValue);
        }
    }

});
