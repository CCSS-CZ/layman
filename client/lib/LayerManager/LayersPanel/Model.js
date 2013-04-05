Ext4.define("HSRSLayerObject", {
        extend: 'Ext4.Base',
        resource: undefined,
        name: undefined,
        style: undefined,
        attribution: undefined,
        type: undefined,
        constructor:function(config) {
            Ext4.Object.merge(this, config);
            this.callParent(arguments);
        }
});
Ext4.define("HSRSFeatureTypeObject", {
        extend: 'Ext4.Base',
        aaa: "FeatureTypeObject",
        nativeBoundingBox: undefined,
        nativeCRS: undefined,
        description: undefined,
        title: undefined,
        latLonBoundingBox: undefined,
        enabled: undefined,
        namespace: undefined,
        projectionPolicy: undefined,
        numDecimals: undefined,
        srs: undefined,
        keywords: undefined,
        attributes: undefined,
        nativeName: undefined,
        maxFeatures: undefined,
        store: undefined,
        name: undefined,
        constructor:function(config) {
            Ext4.Object.merge(this, config);
            this.callParent(arguments);
        }
});

Ext4.data.Types.TYPELAYER = {
    convert: function(v, model) {
        var l = new HSRSLayerObject(v);
        return l;
    },
    sortType: function(v) {
        return v.name;  // When sorting, order by latitude
    },
    type: 'LayerObject'
};

Ext4.data.Types.TYPEFEATURETYPE = {
    convert: function(v, model) {
        return new HSRSFeatureTypeObject(v);
    },
    sortType: function(v) {
        return v.title;  // When sorting, order by latitude
    },
    type: 'TypeFeatureType'
};


Ext4.define('HSRS.LayerManager.LayersPanel.Model', {
        extend: 'Ext4.data.Model',
        fields: [
            {name: 'workspace', mapping: "ws",type: Ext4.data.Types.STRING},
            {name: 'wstitle', mapping: "roleTitle",type: Ext4.data.Types.STRING},
            {name: 'layer', mapping: "layer",type: Ext4.data.Types.TYPELAYER},
            {name: 'featuretype', mapping: "featureType",type: Ext4.data.Types.TYPEFEATURETYPE}
        ]

});

