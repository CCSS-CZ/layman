/**
 * License: ...
 * @author:  Michal
 */

Ext4.define('HSRS.LayerManager.CkanPanel.CkanMenu', {

    extend: 'Ext4.menu.Menu',

    requires: [],

    url: undefined,
    record: undefined,

    /**
     * @constructor
     */
    constructor: function(config) {
        config.title = "Dataset details";
        //config.width = 200;
        config.plain = true;

        this.url = config.url.replace(/\/$/, config.record.get('name'));

        config.name = "Dataset details";

        config.items = [];

        config.items.push({
            text: '<b>' + config.record.get('title') + '</b>'
        });

        config.items.push({
            text: "Resources:"
        });

        // Resources
        resources = arguments[0].record.raw.resources;
        for (var i=0, l=resources.length; i<l; ++i) {

            var newItem = {
                text: resources[i].name,
                scope: {obj: this, urlToGet: resources[i].url},
                handler: this._onResourceClicked
            };

            if resources[i].format != "" {
                newItem.text += '[' + resources[i].format + ']';
            }

            config.items.push(newItem);
        }    

        this.callParent(arguments);

        this.addEvents('copytofiles');
    },

    /**
     * download handler
     * @private
     */
    //_onResourceClicked: function(urlToGet) {
    _onResourceClicked: function() {

        this.obj.fireEvent('copytofiles', this.urlToGet);
     },

    /**
     * on ckan downloaded
     * @private
     * @function
     */
    _onCkanDownloaded: function(data) {
        this.fireEvent('ckandownloaded', data);
    }

});
