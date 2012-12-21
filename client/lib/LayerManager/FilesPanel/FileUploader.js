Ext4.define("HSRS.LayerManager.FilesPanel.FileUploader", {
    
    extend: "Ext4.form.Panel",

    /**
     * @constructor
     */
     constructor: function(config) {

        config.frame = true;
        config.items = [{
            xtype: "textfield",
            id: 'file_name',
            //emptyText: '(leave blank for use file name)',
            fieldLabel: 'New file name',
            name: 'newfilename',
            width: 350,
            labelWidth: 120,
            allowBlank: true
        },
        //{
        //    xtype: "checkbox",
        //    id: 'ovewrite',
        //    fieldLabel: 'Overwrite existing',
        //    name: 'overwrite',
        //    labelWidth: 120
        //},
        {
            xtype: 'filefield',
            id: 'form-file',
            emptyText: 'Select an file',
            fieldLabel: 'File',
            name: 'filename',
            buttonText: '',
            width: 350,
            labelWidth: 120,
            allowBlank: false,
            buttonConfig: {
                icon: HSRS.IMAGE_LOCATION+"/page_add.png"
            }
        }];

        config.buttons = [{
            text: 'Save',
            scope:this,
            handler: function(){
                var form = this.getForm();
                this._onBeforeSubmit();
                if(form.isValid()){
                    form.submit({
                        scope: this,
                        url: config.url,
                        waitMsg: "Uploading files to server ...",
                        success: function(form, action) {
                            this.fireEvent("filesaved",action);
                            Ext.Msg.alert('Success', 'Processed file "' + action.result.file + '" on the server');
                        },
                        failure: function(form, action) {
                            this.fireEvent("filesaved",action);
                            Ext.Msg.alert('Failed', action.result ? action.result.msg : 'No response');
                        }
                    });
                }
            }
        },{
            text: 'Reset',
            handler: function() {
                this.up('form').getForm().reset();
            }
        }];

        this.callParent(arguments);
        
        this.addEvents("filesaved");

     },

     /**
      * on before submit event handler
      * @private
      * @function
      */
     _onBeforeSubmit: function() {
         var form = this.getForm();
         var values = form.getValues();

     }
});
