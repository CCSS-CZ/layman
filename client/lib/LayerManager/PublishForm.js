/**
 * License: ...
 * @author: Jachym, Michal
 */

Ext4.define('HSRS.LayerManager.PublishForm', {

    requires: ['HSRS.LayerManager.PublishForm.LayersCombo',
               'HSRS.LayerManager.PublishForm.ItemSelector'],
    extend: 'Ext4.form.Panel',
    groups: undefined,
    isFeatureType: false,
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
        config.url = config.isFeatureType ? config.url + config.name :
                     config.url;
        this._url = config.url;
        config.buttons = [
            {
                text: config.isFeatureType ? 'Update' : 'Publish',
                id: 'publish_button',
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
                disabled: (config.isFeatureType ? true : false),
                name: 'usergroup',
                id: 'usergroup',
                anchor: '100%',
                fieldLabel: 'Publish to',
                store: Ext4.create('Ext4.data.JsonStore', { // FIXME - this should be done ONCE, not everytime the Publish/Update is clicked
                    autoLoad: true,
                    proxy: {
                        type: 'ajax',
                        url: config.url + 'groups', // Here we get the groups of the user
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

                            /* Select read groups that were specified by the server
                             * Tohle by mlo byt poveseny na read_groups store load - ale tam to kur*a nefacha...
                             * FIXME - we should wait until All Groups response is loaded into the read_groups store                            
                             */
                            if (config.isFeatureType) { // If the layer is already published

                                // Go through the provided list
                                grantList = config.readGroups;
                                for (var i=0, len=grantList.length; i<len; ++i) {
                                    // Click the "Add" button       
                                    // var read_groups = this.form.down('#read_groups');
                                    var read_groups = Ext4.getCmp('read_groups');
                                    var sm = read_groups.fromField.boundList.getSelectionModel();
                                    // if (sm.store.data.length == 0) - jeste neni naloadovany all groups...
                                    sm.select(grantList[i]);
                                    read_groups.onAddBtnClick();
                                }
                            } /**/ 

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
                        if (!this.up().isFeatureType) {
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
                disabled: (config.isFeatureType ? true : true),
                anchor: '100%',
                fieldLabel: 'Publish as',
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
                disabled: (config.isFeatureType ? false : true),
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
                        title: 'Metadata of "' + config.name + '"',
                         items: [
                           /* set name if this is existing feature type
                            */
                           {
                               name: 'layerName',
                               id: 'layerName',
                               xtype: 'hidden',
                               anchor: '100%',
                               value: (config.isFeatureType ?
                                       config.name : undefined)
                           },
                           /* set name of the file if this is file name
                            */
                           {
                               name: 'fileName',
                               id: 'fileName',
                               xtype: 'hidden',
                               disabled: (config.isFeatureType ?
                                          true : false),
                               anchor: '100%',
                               value: (config.isFeatureType ?
                                       undefined : config.name)
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
                               value: config.abstract ||
                                   config.description || ''
                           },
                          /* Keywords field
                           */
                           {
                               fieldLabel: 'Keywords',
                               xtype: 'textfield',
                               anchor: '100%',
                               name: 'keywords',
                               value: config.keywords,
                               id: 'keywords',
                               allowBlank: true
                           },
                          /* Metadata link field
                           */
                           {
                               fieldLabel: 'Metadata link',
                               emptyText: 'http://',
                               anchor: '100%',
                               xtype: 'textfield',
                               name: 'metadataurl',
                               value: config.metadataurl || ''
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
                               value: config.attribution_text ?
                                      config.attribution_text : '',
                               name: 'attribution_text'
                           },
                           {
                               fieldLabel: 'Attribution link',
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
                    title: 'Advanced',
                    items: [
                        /* Read access
                         */
                        {
                            xtype: 'fieldset',
                            anchor: '100%',
                            layout: 'anchor',
                            title: 'Read access',
                            items: [ {
                                xtype: 'itemselector',
                                name: 'read_groups',
                                id: 'read_groups',
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
                                        url: config.url + 'allgroups', // Here we get all the groups
                                        model: 'HSRS.LayerManager.PublishForm.AllGroupModel',
                                        reader: {
                                            type: 'json',
                                            idProperty: 'name'
                                        }
                                    },
                                    /* listeners: { // FIXME It should be here but doesn't work here
                                        /* Select read groups that were specified by the server
                                         * /
                                        load: function(p1, records, ok, opts) {

                                            if (config.isFeatureType) { // If the layer is already published

                                                // Go through the provided list
                                                grantList = config.readGroups;
                                                for (var i=0, len=grantList.length; i<len; ++i) {
                                                    // Click the "Add" button       
                                                    // var read_groups = this.form.down('#read_groups');
                                                    var read_groups = Ext4.getCmp('read_groups');
                                                    var sm = read_groups.fromField.boundList.getSelectionModel();
                                                    sm.select(grantList[i]);
                                                    read_groups.onAddBtnClick();
                                                }
                                            }  
                                        }
                                    },*/
                                    fields: ['name', 'title']
                                }),
                                displayField: 'title',
                                valueField: 'name',
                                allowBlank: true, // Shoudl this be rather false?
                                msgTarget: 'side',
                                fromTitle: 'Available groups',
                                toTitle: 'Groups read'
                            } ]
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
                                     emptyText: "EPSG:",
                                     value: (config.prj == "None:None" || config.prj == '' ? "" : config.prj),
                                     validator: function(val) {
                                        // TODO
                                        return true;
                                     },
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
                    ]
                }]
            }
        ];

        /* Select read groups that were specified by the server
         * /
        if (config.isFeatureType) { // If the layer is already published

            // Go through the provided list
            grantList = config.readGroups;
            for (var i=0, len=grantList.length; i<len; ++i) {
                // Click the "Add" button       
                var read_groups = this.down('#read_groups');
                var sm = read_groups.fromField.boundList.getSelectionModel();
                sm.select(grantList[i]);
                read_groups.onAddBtnClick();
            }
        }*/

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
                   msg: 'Importing data to database, creating new layer ...',
                   progressText: 'Importing file ...',
                   width: 300,
                   wait: true,
                   waitConfig: {interval: 200},
                   icon: 'ext4-mb-download', //custom class in msg-box.html
                   iconHeight: 50
               });
            
            if (this.isFeatureType) { // If it already exists

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
                if (!newLayerData.metadataLinks) {
                    newLayerData.metadataLinks = {}
                }

                // Metadata
                if (!newLayerData.metadataLinks.metadataLink) {
                    newLayerData.metadataLinks.metadataLink = []
                }
                if (!newLayerData.metadataLinks.metadataLink[0]) {
                    newLayerData.metadataLinks.metadataLink[0] = {}
                }
                newLayerData.metadataLinks.metadataLink[0].content =  vals.metadataurl;

                // Layer params

                // Attribution
                if (!newLayer.attribution) {
                    newLayer.attribution = {}
                }
                newLayer.attribution.title = vals.attribution_text;
                newLayer.attribution.href  = vals.attribution_link;

                // PUT Layer Config 

                Ext4.Ajax.request({
                    url: this.url,
                    jsonData: {
                        usergroup:  this.group,     // group=workspace
                        fileName:   vals.fileName,  // wtf?
                        layer:      newLayer,       // "layer" json of geoserver
                        layerData:  newLayerData    // "featureType" or "coverage" json of geoserver
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
                        Ext4.Msg.alert('Failed', 'Settings update failed' +
                            '<br />' + obj.message);
                    },
                    scope: this
                });
            }

            // submit new files using http POST
            else {
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
                        Ext4.Msg.alert('Failed', 'Publishing file failed' +
                            '<br />' + obj.message);
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

            this.isFeatureType = true;
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

            this.isFeatureType = false;
            this.down('#publish_button').setText('Publish');
            this.url = this._url;
            this.down('#layerName').setValue(newValue);
        }
    }

});
