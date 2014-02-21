/**
 * License: ...
 * @author: Jachym, Michal
 */

Ext4.define('HSRS.LayerManager.DataPanel.DataMenu', {

    extend: 'Ext4.menu.Menu',

    requires: [],

    url: undefined,
    record: undefined,

    /**
     * @constructor
     */
    constructor: function(config) {
        config.title = config.record.get('name');
        config.width = 200;
        config.plain = true;

        this.url = config.url.replace(/\/$/, config.record.get('name'));

        config.title = config.record.get('name');
        config.items = [];

        config.items.push({
                text: 'Publish',
                icon: HSRS.IMAGE_LOCATION + '/map_go.png',
                scope: this,
                handler: this._onPublishClicked
            });

        config.items.push(
            { xtype: 'menuseparator' }
        );

        config.items.push({
                text: 'Delete',
                icon: HSRS.IMAGE_LOCATION + '/delete.png',
                scope: this,
                handler: this._onDeleteClicked
            });

        this.callParent(arguments);

        this.addEvents('datadeleted');
        this.addEvents('datapublished');
    },

    /**
     * delete handler
     * @private
     */
    _onDeleteClicked: function() {
        this.fireEvent('datadeleted', this.record);
    },

    /**
     * import handler
     * @private
     */
    _onPublishClicked: function() {
/* TODO: _onPublishClicked
        metadataUrlSafe = (this.layerData.metadataLinks && this.layerData.metadataLinks.metadataLink[0] && this.layerData.metadataLinks.metadataLink[0].content) 
                    ? this.layerData.metadataLinks.metadataLink[0].content
                    : undefined; 

        keywordsSafe = (this.layerData.keywords)
                    ? this.layerData.keywords.string.join(",")
                    : undefined

        var publishForm = Ext4.create('HSRS.LayerManager.PublishForm', {
            name: this.layer.name,
            url: this.url.replace('fileman', 'layed'),
            type: this.layer.type,
            groups: this.groups,
            abstract: this.layerData.description,
            title: this.layerData.title,
            group: this.record.get("workspace"),
            isFeatureType: true,
            prj: this.layerData.srs,
            layerData: this.layerData,
            layer: this.layer,
            readGroups: this.record.raw.readGroups,
            keywords: keywordsSafe,
            metadataurl: metadataUrlSafe,
            attribution_text: this.layer.attribution.title,
            attribution_link: this.layer.attribution.href,
            extent: [this.layerData.latLonBoundingBox.minx,
                     this.layerData.latLonBoundingBox.miny,
                     this.layerData.latLonBoundingBox.maxx,
                     this.layerData.latLonBoundingBox.maxy],
            //attributes: this.featureType.attributes.attribute,
            geomtype: this.layer.type
        });
        publishForm._win = Ext4.create('Ext4.window.Window', {
            title: 'Edit layer attributes',
            items: [publishForm]
        });

        publishForm.on('canceled', publishForm._win.close, publishForm._win);
        publishForm.on('updated',
            function(e) {
                this.publishForm._win.close();
                this.menu._onLayerUpdated.apply(this.menu, arguments);
            },
            {menu: this, publishForm: publishForm}
        );
        publishForm._win.show();
  */ 
                this.menu._onDataPublished.apply(this.menu, arguments);
     },

    /**
     * on file published
     * @private
     * @function
     */
    _onDataPublished: function(data) {
        this.fireEvent('datapublished', data);
    }

});
