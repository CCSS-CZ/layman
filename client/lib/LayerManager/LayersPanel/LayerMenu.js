/**
 * License: ...
 * @author: Jachym
 */

Ext4.define('HSRS.LayerManager.LayersPanel.LayerMenu', {

    extend: 'Ext4.menu.Menu',

    requires: [],

    url: undefined,
    record: undefined,

    /**
     * @constructor
     */
    constructor: function(config) {
        // config.layername = config.record.get('layername');

        config.width = 200;
        config.plain = true;

        this.url = config.url.replace(/\/$/, config.record.get('layername'));

        config.items = [];

        if (HSRS && HSRS.VIEWURL) {
            config.items.push(
                {
                    text: 'Add to map',
                    icon: HSRS.IMAGE_LOCATION + '/map_go.png',
                    scope: this,
                    handler: this._onViewClicked
                }
            );

        }

        if (HSRS && HSRS.STYLERURL) {
            config.items.push({
                text: 'Styler',
                icon: HSRS.IMAGE_LOCATION + '/style.png',
                scope: this,
                handler: this._onStyleClicked
            });
        }

        config.items.push({
                text: 'Settings',
                icon: HSRS.IMAGE_LOCATION + '/cog.png',
                scope: this,
                handler: this._onSettingsClicked
            });

        config.items.push(
            { xtype: 'menuseparator' }
        );

        config.items.push({
                text: 'Delete layer and data',
                icon: HSRS.IMAGE_LOCATION + '/delete.png',
                scope: this,
                handler: this._onDeleteClicked
            });

        config.items.push({
                text: 'Delete layer only',
                icon: HSRS.IMAGE_LOCATION + '/delete.png',
                scope: this,
                handler: this._onDeleteOnlyClicked
            });

        this.callParent(arguments);

        this.addEvents('layerdeleted');
        this.addEvents('layeronlydeleted');
        this.addEvents("layerupdated");
    },

    /**
     * delete handler
     * @private
     */
    _onDeleteClicked: function() {
        this.fireEvent('layerdeleted', this.record);
    },

    _onDeleteOnlyClicked: function() {
        this.fireEvent('layeronlydeleted', this.record);
    },

    /**
     * style handler
     * @private
     */
    _onStyleClicked: function() {
        stylerUrl = HSRS.STYLERURL.replace("layerData.name", "layername")
        var t = new Ext4.XTemplate(stylerUrl);
        var url = t.apply(this.record.data);
        //window.open(url, '_newtab');
        window.location = url;
    },

    /**
     * import handler
     * @private
     */
    _onSettingsClicked: function() {

        metadataUrlSafe = (this.layerData.metadataLinks && this.layerData.metadataLinks.metadataLink[0] && this.layerData.metadataLinks.metadataLink[0].content) 
                    ? this.layerData.metadataLinks.metadataLink[0].content
                    : undefined; 

        keywordsSafe = (this.layerData.keywords)
                    ? this.layerData.keywords.string.join(",")
                    : undefined

        attributionTitleSafe = this.layer.attribution ? this.layer.attribution.title : undefined
        attributionHrefSafe  = this.layer.attribution ? this.layer.attribution.href : undefined

        var publishForm = Ext4.create('HSRS.LayerManager.PublishForm', {
            name: this.layer.name,
            url: this.url.replace('fileman', 'layed'),
            type: this.layer.type,
            groups: this.groups,
            abstract: this.layerData.description,
            title: this.layerData.title,
            group: this.record.get("workspace"),
            type: "layer",
            prj: this.layerData.srs,
            layerData: this.layerData,
            layer: this.layer,
            secureLayer: this.record.raw.secureLayer,
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
    },

    /**
     * on file published
     * @private
     * @function
     */
    _onLayerUpdated: function(data) {
        this.fireEvent('layerupdated', data);
    },

    /**
     * view handler
     * @private
     */
    _onViewClicked: function() {
        viewUrl = HSRS.VIEWURL.replace("layerData.name", "layername");
        //var t = new Ext4.XTemplate(HSRS.VIEWURL);
        var t = new Ext4.XTemplate(viewUrl);
        var url = t.apply(this.record.data);
        //window.open(url, '_newtab');
        window.location = url;
    }

});
