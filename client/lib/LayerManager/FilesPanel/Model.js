Ext.define('HSRS.LayerManager.FilesPanel.Model', {
        extend: 'Ext.data.Model',
        fields: [
            {name: 'name',     type: 'string'},
            {name: 'size',     type: 'string'},
            {name: 'prj',      type: 'string'},
            {name: 'mimetype', type: 'string'}
        ]
});
