
Ext4.define('HSRS.LayerManager.CkanPanel.Model', {
        extend: 'Ext4.data.Model',
        fields: [
            {name: 'organizationName', mapping: 'organizationName', type: Ext4.data.Types.STRING},
            {name: 'organizationTitle', mapping: 'organizationTitle', type: Ext4.data.Types.STRING},
            {name: 'name',  mapping: 'name', type: Ext4.data.Types.STRING},
            {name: 'title',  mapping: 'title', type: Ext4.data.Types.STRING},
            {name: 'notes',  mapping: 'notes', type: Ext4.data.Types.STRING}
        ]

});

