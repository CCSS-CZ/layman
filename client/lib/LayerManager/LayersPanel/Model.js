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

Ext4.define('HSRSLayerObject', { // Obsolete
        extend: 'Ext4.Base',
        resource: undefined,
        name: undefined,
        style: undefined,
        attribution: undefined,
        type: undefined,
        constructor: function(config) {
            Ext4.Object.merge(this, config);
            this.callParent(arguments);
        }
});

Ext4.define('HSRSLayerDataObject', { // Obsolete
        extend: 'Ext4.Base',
        aaa: 'CoverageTypeObject',
        nativeBoundingBox: undefined, //
        nativeCRS: undefined, //
        description: undefined, //
        title: undefined, //
        latLonBoundingBox: undefined, //
        enabled: undefined, //
        namespace: undefined, //
        projectionPolicy: undefined, //
        srs: undefined, //
        nativeName: undefined, //
        store: undefined, //
        name: undefined, //
        // datatype: undefined, // should not be here
        constructor: function(config) {
            Ext4.Object.merge(this, config);
            this.callParent(arguments);
        }
});

Ext4.data.Types.TYPELAYER = { // Obsolete
    convert: function(v, model) {
        var l = new HSRSLayerObject(v);
        return l;
    },
    sortType: function(v) {
        return v.name;  
    },
    type: 'LayerObject'
};

Ext4.data.Types.LAYERDATATYPE = { // Obsolete
    convert: function(v, model) {
        return new HSRSLayerDataObject(v);
    },
    sortType: function(v) {
        return v.title;  
    },
    type: 'LayerDataType'
};

Ext4.define('HSRS.LayerManager.LayersPanel.Model', {
        extend: 'Ext4.data.Model',
        fields: [
            {name: 'workspace', mapping: 'layergroup', type: Ext4.data.Types.STRING},
            {name: 'wstitle', mapping: 'roleTitle', type: Ext4.data.Types.STRING},
            {name: 'layertitle', mapping: 'layertitle', type: Ext4.data.Types.STRING},
            {name: 'layername',  mapping: 'layername', type: Ext4.data.Types.STRING},
            {name: 'layertype',  mapping: 'layertype', type: Ext4.data.Types.STRING},
            {name: 'datatype',  mapping: 'datatype', type: Ext4.data.Types.STRING},
            {name: 'vectortype',  mapping: 'vectortype', type: Ext4.data.Types.STRING},
            {name: 'owner',  mapping: 'owner', type: Ext4.data.Types.STRING},
            {name: 'datagroup',  mapping: 'datagroup', type: Ext4.data.Types.STRING},
            {name: 'dataname',  mapping: 'dataname', type: Ext4.data.Types.STRING}
        ]
});

