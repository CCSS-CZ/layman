/**
 * License: ...
 * @author: Jachym
 */

Ext4.define("HSRS.LayerManager.FilesPanel.FileMenu", {
    
    extend: "Ext4.menu.Menu",

    requires:["HSRS.LayerManager.UploadForm"],

    file: undefined,
    data: undefined, 
    
    /**
     * @constructor
     */
    constructor: function(config) {
        config.title = config.data.name;
        config.width = 200;
        config.plain = true;
        config.items = [
            {
                plain: true,
                text: "Size: "+config.data.size
            },
            {
                plain: true,
                text: "Projection: "+config.data.prj
            },
            {
                plain: true,
                text: "Date: "+config.data.date
            },
            {
                plain: true,
                text: "Type: "+config.data.mimetype
            },
            {
                plain: true,
                text: "Features count: "+config.data.features
            },
            {
                plain: true,
                text: "Geometry: "+config.data.geomtype
            },
            {
                xtype: "menuseparator"
            },
            {
                text: "Delete",
                icon: HSRS.IMAGE_LOCATION+"/delete.png",
                scope: this,
                handler: this._onDeleteClicked
            },
            {
                text: "Publish",
                icon: HSRS.IMAGE_LOCATION+"/import.png",
                scope: this,
                handler: this._onUploadClicked
            }
        ];

        this.callParent(arguments);
    },

    /**
     * delete handler
     * @private
     */
    _onDeleteClicked: function() {
        alert ("Deleting "+this.record.get("name")+". To be implemented");
    },

    /**
     * import handler
     * @private
     */
    _onUploadClicked: function() {
        var uploadForm = Ext4.create("HSRS.LayerManager.UploadForm", {
            name: this.data.name,
            type: this.data.type,
            prj: this.data.prj,
            attributes: this.data.attributes,
            geomtype: this.data.geomtype
        });
        uploadForm._win = Ext4.create("Ext4.window.Window", {
            title: "Upload and publish file to GeoServer",
            items: [uploadForm]
        });
        uploadForm._win.show();
    }
});
