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

            config.items.push({
                text: resources[i].name,
                scope: {obj: this, urlToGet: resources[i].url},
                handler: this._onResourceClicked,
                // urlToGet: resources[i].url
                // handler: this._onResourceClicked(resources[i].url)
                // href: resources[i].url
                // hrefTarget: '_blank' 
            });
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
/*
        //TODO: get fileman url
        var filemanUrl = "http://erra.ccss.cz/cgi-bin/layman/layman/fileman/"
        var url = filemanUrl + '?source=url&url=' + urlToGet;
        console.log(url);
        Ext4.Ajax.request({
            method: 'POST',
            url: (HSRS.ProxyHost ? HSRS.ProxyHost + escape(url) : url),
            success: function() {
                // TODO - handle returned message
            },
            scope: this
        });

        // TODO: Re-load Files Panel
        // this.store.load();
*/
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
