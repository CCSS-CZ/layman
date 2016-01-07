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
                    title: HS.i18n("New layer")
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
