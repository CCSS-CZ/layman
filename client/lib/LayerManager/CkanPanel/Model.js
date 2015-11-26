
// Model for getCkanResources()
Ext4.define('HSRS.LayerManager.CkanPanel.ResourceModel', {
        extend: 'Ext4.data.Model',
        fields: [
            {name: 'name', mapping: 'name', type: Ext4.data.Types.STRING},
            {name: 'url', mapping: 'url', type: Ext4.data.Types.STRING},
            {name: 'format', mapping: 'format', type: Ext4.data.Types.STRING},
            {name: 'description', mapping: 'description', type: Ext4.data.Types.STRING}
        ]

});

// Model for getCkanPackages() (datasets)
Ext4.define('HSRS.LayerManager.CkanPanel.PackageModel', {
        extend: 'Ext4.data.Model',
        fields: [
            {name: 'organizationName', mapping: 'organizationName', type: Ext4.data.Types.STRING},
            {name: 'organizationTitle', mapping: 'organizationTitle', type: Ext4.data.Types.STRING},
            {name: 'name',  mapping: 'name', type: Ext4.data.Types.STRING},
            {name: 'title',  mapping: 'title', type: Ext4.data.Types.STRING},
            {name: 'notes',  mapping: 'notes', type: Ext4.data.Types.STRING}
        ]

});

