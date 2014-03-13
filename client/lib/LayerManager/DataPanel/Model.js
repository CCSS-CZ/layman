
Ext4.define('HSRS.LayerManager.DataPanel.Model', {
        extend: 'Ext4.data.Model',
        fields: [
            {name: 'schema', mapping: 'schema', type: Ext4.data.Types.STRING},
            {name: 'schemaTitle', mapping: 'roleTitle', type: Ext4.data.Types.STRING},
            {name: 'name',  mapping: 'name', type: Ext4.data.Types.STRING},
            {name: 'type',  mapping: 'type', type: Ext4.data.Types.STRING}
        ]

});

