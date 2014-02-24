
Ext4.define('HSRS.LayerManager.DataPanel.Model', {
        extend: 'Ext4.data.Model',
        fields: [
            {name: 'schema', mapping: 'schema', type: Ext4.data.Types.STRING},
            {name: 'schemaTitle', mapping: 'roleTitle', type: Ext4.data.Types.STRING},
            {name: 'name',  mapping: 'table', type: Ext4.data.Types.STRING}
        ]

});

