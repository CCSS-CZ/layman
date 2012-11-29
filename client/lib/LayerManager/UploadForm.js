/**
 * License: ...
 * @author: Jachym
 */

Ext4.define("HSRS.LayerManager.UploadForm", {
    
    extend: "Ext4.form.Panel",

    /**
     * @constructor
     */
    constructor: function(config) {
        config.items = this._initItems(config);

        this.callParent(arguments);
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
            {
                fieldLabel: 'Keywords',
                xtype: 'multiselect',
                anchor: '100%',
                msgTarget: 'side',
                name: 'keywords',
                allowBlank: true,
                store: {
                    fields: [ 'keyword' ],
                    data: [["keyword1"]]
                },
                valueField: 'keyword',
                displayField: 'keyword'
            },
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
                items: [
                    {
                        fieldLabel: "Native SRS",
                        value: config.data.crs,
                        name: "crs"
                    }
                ]
            },
            {
                title:"Bounding Boxes",
                xtype:"fieldset",
                anchor:"100%",
                items: [
                    {
                        fieldLabel:""
                    }
                ]
            }
        ];
    }
});
