/*
    LayMan - the Layer Manager

    Copyright (C) 2016 Czech Centre for Science and Society
    Authors: Jachym Cepicky, Karel Charvat, Stepan Kafka, Michal Sredl, Premysl Vohnout
    Mailto: sredl@ccss.cz, charvat@ccss.cz

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
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

        config.name = config.record.get('name');
        config.schema = config.record.get('schema');
        config.items = [];

        config.items.push({
                text: HS.i18n('Publish'),
                icon: HSRS.IMAGE_LOCATION + '/map_go.png',
                scope: this,
                handler: this._onPublishClicked
            });

        config.items.push(
            { xtype: 'menuseparator' }
        );

        this.callParent(arguments);

        this.addEvents('datapublished');
    },

    /**
     * import handler
     * @private
     */
    _onPublishClicked: function() {

        var publishForm = Ext4.create('HSRS.LayerManager.PublishForm', {
            name: this.name,
            url: this.url.replace('data', 'layers'),
            groups: this.groups,
            group: this.schema,
            datatype: this.record.data.datatype,
            layertype: this.record.data.layertype,
            owner: this.record.data.owner,
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
