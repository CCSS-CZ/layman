Ext4.define('HSRS.LayerManager.PublishForm.LayersCombo', {

    extend: "Ext4.form.field.ComboBox", 
    alias: ['widget.layerscombo'],

    constructor: function(config){

        config.editable =  false;
        config.displayField = 'title';
        config.valueField = 'name';
        
        config.store = Ext4.create('Ext4.data.JsonStore', {
            autoLoad: true,
            data:[
                Ext4.create("HSRS.LayerManager.LayersPanel.Model",{
                    name:"newlayer",
                    title:"New layer"
                })
            ],
            proxy: {
                type: "ajax",
                url: config.url,
                model: 'HSRS.LayerManager.LayersPanel.Model',
                reader: {
                    type: "json" 
                }
            }
        });

        this.callParent(arguments);

        //this._store.on("load",this._onStoreLoad, this);
        //this._store.load();
    },

    loadLayers: function(group) {
        var i, ilen;
        for (i = 0, ilen = this.store.filters.length; i < ilen; i++) {
            this.store.removeFilter(this.store.filters.getAt(0));
        }
                
        this.store.addFilter(
            Ext4.util.Filter({
                property: "workspace",
                value: group
            })
        );
    }

});            
