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
        config.title = config.record.get('title');
        //config.width = 200;
        config.plain = true;

        this.url = config.url.replace(/\/$/, config.record.get('name'));

        config.name = config.record.get('name');
        // config.schema = config.record.get('schema'); // replace with organization ?

        config.items = [];

        /*
        config.items.push({
                text: HS.i18n('Download'),
                // icon: HSRS.IMAGE_LOCATION + '/map_go.png',
                scope: this,
                handler: this._onDownloadClicked
            });

        config.items.push(
            { xtype: 'menuseparator' }
        );
        */

        // Resources
        resources = arguments[0].record.raw.resources;
        for (var i=0, l=resources.length; i<l; ++i) {

            config.items.push({
                text: '<a href="'+ resources[i].url + '">' + resources[i].name + '</a>'
            });
        }    

        this.callParent(arguments);

        this.addEvents('ckandownloaded');
    },

    /**
     * download handler
     * @private
     */
    _onDownloadClicked: function() {
/* TODO - download dataset
        var publishForm = Ext4.create('HSRS.LayerManager.PublishForm', {
            name: this.name,
            url: this.url.replace('fileman', 'publish'),
            groups: this.groups,
            group: this.schema,
            type: "data"
        });
        publishForm._win = Ext4.create('Ext4.window.Window', {
            title: HS.i18n('Publish'),
            items: [publishForm]
        });

        publishForm.on('canceled', publishForm._win.close, publishForm._win);
        publishForm.on('published',
            function(e) {
                this.publishForm._win.close();
                this.menu._onDataPublished.apply(this.menu, arguments);
            },
            {menu: this, publishForm: publishForm}
        );
        publishForm._win.show();
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
