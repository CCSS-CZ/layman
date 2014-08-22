/**
 * License: ...
 * @author: Jachym
 */

Ext4.define('HSRS.LayerManager.FilesPanel.FileMenu', {

    extend: 'Ext4.menu.Menu',

    requires: ['HSRS.LayerManager.PublishForm',
              'HSRS.LayerManager.FilesPanel.Preview'],

    file: undefined,
    data: undefined,
    url: undefined,
    record: undefined,
    prj: undefined,
    tsrs: undefined,
    groups: undefined,

    /**
     * @constructor
     */
    constructor: function(config) {
        config.title = config.data.name;
        config.width = 200;
        config.plain = true;

        this.url = config.url.replace(/\/$/, '');

        config.items = [
            {
                plain: true,
                text: HSRS.formatSize(config.data.size),
                renderTpl: ['<b>'+HS.i18n('Size') +':</b>{text}']
            },
            {
                plain: true,
                text: config.data.prj,
                renderTpl: ['<b>'+HS.i18n('Projection') +': </b>{text}']
            },
            {
                plain: true,
                text: config.data.date,
                renderTpl: ['<b>'+HS.i18n('Date') +': </b>{text}']
            },
            {
                plain: true,
                text: config.data.mimetype,
                renderTpl: ['<b>'+HS.i18n('Type') +': </b>{text}']
            },
            {
                plain: true,
                text: config.data.features_count,
                renderTpl: ['<b>'+HS.i18n('Features count') +': </b>{text}']
            },
            {
                plain: true,
                text: config.data.type,
                renderTpl: ['<b>'+HS.i18n('Geometry type') +' </b>{text}']
            },
            { xtype: 'menuseparator' },
            {
                text: HS.i18n('Publish'),
                icon: HSRS.IMAGE_LOCATION + '/map_go.png',
                scope: this,
                disabled: config.data.extent ? false : true,
                handler: this._onUploadClicked
            },
            {
                text: HS.i18n('Download'),
                icon: HSRS.IMAGE_LOCATION + '/download.png',
                href: this.url + '/' + config.data.name,
                hrefTarget: '_blank'
            },
            {
                text: HS.i18n('Delete'),
                icon: HSRS.IMAGE_LOCATION + '/delete.png',
                scope: this,
                handler: this._onDeleteClicked
            }
        ];

        if (window.OpenLayers && config.data.extent) {
            config.items.push({ xtype: 'menuseparator' });
            config.items.push({
                    text: HS.i18n('Show extent'),
                    icon: HSRS.IMAGE_LOCATION + '/map.png',
                    scope: this,
                    handler: this._previewClicked
                });
        }

        this.callParent(arguments);

        this.addEvents('filepublished');
        this.addEvents('fileupdated');
        this.addEvents('filedeleted');
    },

    /**
     * delete handler
     * @private
     */
    _onDeleteClicked: function() {
        this.fireEvent('filedeleted', this.record);
    },

    /**
     * preview data
     * @private
     */
    _previewClicked: function() {
        var preview = Ext4.create('HSRS.LayerManager.FilesPanel.Preview',
                {
                    data: this.data
                });
        preview._win = Ext4.create('Ext4.window.Window', {
            title: HS.i18n('Extent preview'),
            width: 512,
            height: 300,
            layout: 'fit',
            items: [
                preview
            ]
        });
        preview._win.show();
    },

    /**
     * import handler
     * @private
     */
    _onUploadClicked: function() {
        var publishForm = Ext4.create('HSRS.LayerManager.PublishForm', {
            name: this.data.name,
            url: this.url.replace('fileman', 'layed'),
            type: this.data.type,
            groups: this.groups,
            prj: this.data.prj,
            tsrs: this.srid,
            extent: this.data.extent,
            attributes: this.data.attributes,
            geomtype: this.data.geomtype,
            type: "file"
        });
        publishForm._win = Ext4.create('Ext4.window.Window', {
            title: HS.i18n('Import and publish'),
            items: [publishForm]
        });

        publishForm.on('canceled', publishForm._win.close, publishForm._win);
        publishForm.on('published',
            function(e) {
                this.publishForm._win.close();
                this.menu._onFilePublished.apply(this.menu, arguments);
            },
            {menu: this, publishForm: publishForm}
        );
        publishForm.on('updated',
            function(e) {
                this.publishForm._win.close();
                this.menu._onFileUpdated.apply(this.menu, arguments);
            },
            {menu: this, publishForm: publishForm}
        );
        publishForm._win.show();
    },

    /**
     * on file updated
     * @private
     * @function
     */
    _onFileUpdated: function(data) {

        this.fireEvent('fileupdated', data);
    },

    /**
     * on file published
     * @private
     * @function
     */
    _onFilePublished: function(data) {

        this.fireEvent('filepublished', data);
    }
});
