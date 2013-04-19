/**
 * License: ...
 * @author: Jachym
 */

Ext4.define('HSRS.LayerManager.LayersPanel.LayerMenu', {

    extend: 'Ext4.menu.Menu',

    requires: [],

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

        this.url = config.url.replace(/\/$/, config.record.get('name'));

        config.title = config.record.get('featuretype').title;
        config.items = [];

        var separator = false;

        if (HSRS && HSRS.VIEWURL) {
            separator = true;
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
            separator = true;
            config.items.push({
                text: 'Styler',
                icon: HSRS.IMAGE_LOCATION + '/style.png',
                scope: this,
                handler: this._onStyleClicked
            });
        }

        if (separator) {
            config.items.push(
                { xtype: 'menuseparator' }
            );
        }

        config.items.push({
                text: 'Delete',
                icon: HSRS.IMAGE_LOCATION + '/delete.png',
                scope: this,
                handler: this._onDeleteClicked
            });

        this.callParent(arguments);

        this.addEvents('layerdeleted');
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
        window.open(url, '_newtab');
    },

    /**
     * view handler
     * @private
     */
    _onViewClicked: function() {
        var t = new Ext4.XTemplate(HSRS.VIEWURL);
        var url = t.apply(this.record.data);
        window.open(url, '_newtab');
    }

});
