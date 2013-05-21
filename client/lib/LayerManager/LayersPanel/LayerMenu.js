/**
 * License: ...
 * @author: Jachym
 */

Ext4.define('HSRS.LayerManager.LayersPanel.LayerMenu', {

    extend: 'Ext4.menu.Menu',

    requires: [],

    featureType: undefined,
    layer: undefined,
    url: undefined,
    record: undefined,

    /**
     * @constructor
     */
    constructor: function(config) {
        config.title = config.record.get('name');
        config.width = 200;
        config.plain = true;
        config.layer = config.record.get('layer');
        config.featureType = config.record.get('featuretype');

        this.url = config.url.replace(/\/$/, config.record.get('name'));

        config.title = config.record.get('featuretype').title;
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
                text: 'Delete',
                icon: HSRS.IMAGE_LOCATION + '/delete.png',
                scope: this,
                handler: this._onDeleteClicked
            });

        this.callParent(arguments);

        this.addEvents('layerdeleted');
        this.addEvents("layerupdated");
    },

    /**
     * delete handler
     * @private
     */
    _onDeleteClicked: function() {
        this.fireEvent('layerdeleted', this.record);
    },

    /**
     * style handler
     * @private
     */
    _onStyleClicked: function() {
        var t = new Ext4.XTemplate(HSRS.STYLERURL);
        var url = t.apply(this.record.data);
        //window.open(url, '_newtab');
        window.location = url;
    },

    /**
     * import handler
     * @private
     */
    _onSettingsClicked: function() {

        var publishForm = Ext4.create('HSRS.LayerManager.PublishForm', {
            name: this.layer.name,
            url: this.url.replace('fileman', 'layed'),
            type: this.layer.type,
            groups: this.groups,
            abstract: this.featureType.abstract,
            title: this.featureType.title,
            group: this.record.get("workspace"),
            isFeatureType: true,
            prj: this.featureType.srs,
            featureType: this.featureType,
            layer: this.layer,
            extent: [this.featureType.latLonBoundingBox.minx,
                     this.featureType.latLonBoundingBox.miny,
                     this.featureType.latLonBoundingBox.maxx,
                     this.featureType.latLonBoundingBox.maxy],
            attributes: this.featureType.attributes.attribute,
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
        var t = new Ext4.XTemplate(HSRS.VIEWURL);
        var url = t.apply(this.record.data);
        //window.open(url, '_newtab');
        window.location = url;
    }

});
