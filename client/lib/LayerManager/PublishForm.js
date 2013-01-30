/**
 * License: ...
 * @author: Jachym
 */

Ext4.define("HSRS.LayerManager.PublishForm", {
    
    extend: "Ext4.form.Panel",

    /**
     * @constructor
     */
    constructor: function(config) {
        config.items = this._initItems(config);
        config.layout = "anchor";
        config.frame = true;
        config.buttons = [
            {
                text:"Publish",
                scope: this,
                handler: this._onPublishClicked
            },
            {
                text:"Reset",
                scope: this,
                handler: this._onResetClicked
            },
            {
                text:"Cancel",
                scope: this,
                handler: this._onCancelClicked
            }
        ];

        this.callParent(arguments);

        this.addEvents("published","canceled","reset");
    },

    /**
     * @function
     * @private
     */
    _initItems: function(config) {
        var items = [
            {
                name: "file",
                xtype: "hidden",
                anchor: '100%',
                value: config.name
            },
            {
                fieldLabel: "Title",
                xtype: "textfield",
                anchor: '100%',
                name: "title",
                value: config.name
            },
            {
                fieldLabel: "Abstract",
                xtype: "textfield",
                anchor: '100%',
                name: "abstract",
                value: config.abstract
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
                fieldLabel: "Metadata link",
                anchor:"100%",
                xtype: "textfield",
                name:"metadataurl",
                value: config.metadataurl
            },
            {
                title: "Coordinate Reference Systems",
                anchor:"100%",
                xtype: "fieldset",
                layout: "anchor",
                items: [
                    {
                        fieldLabel: "Native SRS",
                        anchor:"100%",
                        xtype: "textfield",
                        value: config.prj,
                        name: "crs"
                    }
                ]
            },
            {
                title:"Bounding Box",
                xtype:"fieldset",
                anchor:"100%",
                items: [
                    {
                        fieldLabel:"Bounds",
                        hideLabel: true,
                        xtype: "fieldcontainer",
                        name: "bbox",
                        anchor: "100%",
                        layout: {
                            type: "table",
                            columns: 3
                        },
                        defaults: {
                            xtype: "container",
                            width: 75
                        },
                        items: [
                            { html :' ' },
                            {
                                name:"maxy",
                                xtype: "textfield",
                                value: config.extent[0]
                            },
                            { html :' ' },
                            {
                                name:"minx",
                                xtype: "textfield",
                                value: config.extent[1]
                            },
                            { html :' ' },
                            {
                                name:"maxx",
                                xtype: "textfield",
                                value: config.extent[2]
                            },
                            { html :' ' },
                            {
                                name:"miny",
                                xtype: "textfield",
                                value: config.extent[3]
                            },
                            { html :' ' }
                        ]
                    }
                ]
            },
            {
                title: "Attribution",
                anchor:"100%",
                xtype: "fieldset",
                layout: "anchor",
                items: [
                    {
                        fieldLabel: "Attribution text",
                        anchor:"100%",
                        xtype: "textfield",
                        value: config.attribution ? config.attribution.text: "",
                        name: "attribution_text"
                    },
                    {
                        fieldLabel: "Attribution link",
                        anchor:"100%",
                        xtype: "textfield",
                        emptyText: "http://",
                        value: config.attribution ? config.attribution.link :"",
                        name: "attribution_link"
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
        var data = this.getForm().getValues();
        this.fireEvent("published",data);
        
    },
    /*
     * @private
     */
    _onResetClicked: function() {
        this.fireEvent("reset");
        this.getForm().reset();
    },

    /*
     * @private
     */
    _onCancelClicked: function() {
        this.fireEvent("canceled");
    }
});