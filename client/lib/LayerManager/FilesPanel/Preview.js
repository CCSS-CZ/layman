
/**
 * License: ...
 * @author: Jachym
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

        OpenLayers.DOTS_PER_INCH = 90.714236728598;
        this.map = new OpenLayers.Map({
            numZoomLevels: 22,
            layers: [
                new OpenLayers.Layer.OSM('OpenStreetMap',undefined, {isBaseLayer: true}),
                new OpenLayers.Layer.Boxes('Bounds',{isBaseLayer: false})
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
        this.to = new OpenLayers.Projection('epsg:900913');

        this.addBBOX();

        this.maprendered = true;
   },

    addBBOX: function() {

        // wait.till projection is loaded
        if (this.to.proj.readyToUse === false) {
            timer = new HSRS.timer(this.addBBOX, this);
            timer.pause();
        }
        // all projection loaded, add bounds, zoom the map
        else {

            // fix the region - whole world does not work properly
            if (this.data.extent[0] <= -179) {
                this.data.extent[0] = -179;
            }
            if (this.data.extent[1] <= -89) {
                this.data.extent[1] = -89;
            }
            if (this.data.extent[2] >= 179) {
                this.data.extent[2] = 179;
            }
            if (this.data.extent[3] >= 89) {
                this.data.extent[3] = 89;
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
