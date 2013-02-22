
/**
 * License: ...
 * @author: Jachym
 */

Ext4.define("HSRS.LayerManager.FilesPanel.Preview", {
    
    extend: "Ext4.panel.Panel",

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
                new OpenLayers.Layer.OSM("OpenStreetMap"),
                new OpenLayers.Layer.Boxes("Bounds")
            ]
        });

        this.callParent(arguments);
        this.on("afterlayout",this._onAfterLayout,this);
    },

    _onAfterLayout: function() {
        if (this.maprendered) { return; }

        this.map.render(this.body.dom);


        this.from = new OpenLayers.Projection(this.data.prj);
        this.to = new OpenLayers.Projection("epsg:900913");

        this.addBBOX();

        this.maprendered = true;
   },

    addBBOX: function() {

        // wait.till projection is loaded
        if (this.to.proj.readyToUse === false) {
            timer = new HSRS.timer(this.addBBOX,this);
            timer.pause();
        }
        // all projection loaded, add bounds, zoom the map
        else  {

            var bounds = new OpenLayers.Bounds(
                this.data.extent[0],
                this.data.extent[1],
                this.data.extent[2],
                this.data.extent[3]
            );
            // should come from menu, precashed
            bounds.transform(this.from,this.to);

            this.map.layers[1].addMarker(new OpenLayers.Marker.Box(bounds));

            this.map.zoomToExtent(bounds);
        }

    }
});
