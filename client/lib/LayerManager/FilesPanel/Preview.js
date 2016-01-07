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

Ext4.define('HSRS.LayerManager.FilesPanel.Preview', {

    extend: 'Ext4.panel.Panel',

    data: undefined,
    map: undefined,
    from: undefined,
    to: undefined,
    maprendered: false,

    /**
     * @constructor
     */
    constructor: function(config) {

        this.map = new OpenLayers.Map({
            layers: [
                new OpenLayers.Layer.OSM('OpenStreetMap',undefined),
                new OpenLayers.Layer.Boxes('Bounds')
            ]
        });

        this.callParent(arguments);
        this.on('afterlayout', this._onAfterLayout, this);
        this.on('destroy', this._onDestroy, this);
    },

    _onAfterLayout: function() {
        if (this.maprendered) { return; }

        this.map.render(this.body.dom.firstChild.firstChild);


        this.from = new OpenLayers.Projection(this.data.prj);
        this.to = new OpenLayers.Projection('epsg:3857');

        this.addBBOX();

        this.maprendered = true;
   },

    addBBOX: function() {

        // wait.till projection is loaded
        if (this.from.proj.readyToUse === false || this.to.proj.readyToUse === false) {
            timer = new HSRS.timer(this.addBBOX, this);
            timer.pause();
        }
        // all projection loaded, add bounds, zoom the map
        else {

            // fix the region - whole world does not work properly
            if (this.from.proj.srsProjNumber == "4326") {
                if (this.data.extent[0] <= -168.75) {
                    this.data.extent[0] = -168.75;
                }
                if (this.data.extent[1] <= -57) {
                    this.data.extent[1] = -57;
                }
                if (this.data.extent[2] >= 178.6) {
                    this.data.extent[2] = 178.6;
                }
                if (this.data.extent[3] >= 75.3) {
                    this.data.extent[3] = 75.3;
                }
            }

            var bounds = new OpenLayers.Bounds(
                this.data.extent[0],
                this.data.extent[1],
                this.data.extent[2],
                this.data.extent[3]
            );
            // should come from menu, precashed
            bounds.transform(this.from, this.to);

            this.map.layers[1].addMarker(new OpenLayers.Marker.Box(bounds));

            this.map.zoomToExtent(bounds);
        }

    },

    _onDestroy: function() {
        this.map.destroy();
    }

});
