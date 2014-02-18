Ext4.define('HSRS.LayerManager.FilesPanel.Model', {
        extend: 'Ext.data.Model',
        fields: [
            {name: 'name', type: 'string'},
            {name: 'date', type: 'string'},
            {name: 'size', type: 'string'},
            {name: 'prj', type: 'string'},
            {name: 'tsrs', type: 'string'},
            {name: 'type', type: 'string'},
            {name: 'extent', type: 'array'},
            {name: 'mimetype', type: 'string'}
        ]
});
