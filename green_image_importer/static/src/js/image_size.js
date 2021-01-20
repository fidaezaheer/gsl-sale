odoo.define('green_image_importer.basic_fields', function (require) {
    "use strict";
    
    var AbstractFieldBinary = require('web.basic_fields').AbstractFieldBinary;
    
    var AbstractFieldBinary = AbstractFieldBinary.include({
        init: function (parent, name, record) {
            this._super.apply(this, arguments);
            this.fields = record.fields;
            this.useFileAPI = !!window.FileReader;
            this.max_upload_size = 250 * 1024 * 1024; // 64Mo
            this.accepted_file_extensions = (this.nodeOptions && this.nodeOptions.accepted_file_extensions) || this.accepted_file_extensions || '*';
            if (!this.useFileAPI) {
                var self = this;
                this.fileupload_id = _.uniqueId('o_fileupload');
                $(window).on(this.fileupload_id, function () {
                    var args = [].slice.call(arguments).slice(1);
                    self.on_file_uploaded.apply(self, args);
                });
            }
        },
    });
    
    return {
        AbstractFieldBinary: AbstractFieldBinary,
    };
    
    });
    