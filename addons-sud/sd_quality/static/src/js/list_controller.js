odoo.define('besco_stock.ListController', function (require) {
"use strict";

    var ListController = require('web.ListController');

    ListController.include({
        /**
         * This helper simply makes sure that the control panel buttons matches the
         * current mode.
         *
         * @param {string} mode either 'readonly' or 'edit'
         */
        _updateButtons: function (mode) {
            if (this.$buttons) {
                this.$buttons.toggleClass('o-editing', mode === 'edit');
                const state = this.model.get(this.handle, {raw: true});
                this.$('.o_list_export_xlsx').show();
                // THANH 13042020 display export toool to help in template import for inventory count sheet
//                if (state.count) {
//                    this.$('.o_list_export_xlsx').show();
//                } else {
//                    this.$('.o_list_export_xlsx').hide();
//                }
            }
        },
    });

});
