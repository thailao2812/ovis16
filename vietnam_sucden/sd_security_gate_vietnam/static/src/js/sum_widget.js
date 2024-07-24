odoo.define('sd_security_gate_vietnam.ListRenderer', function (require) {
  'use strict';

  var ListRenderer = require('web.ListRenderer');

  ListRenderer.include({

    /**
     * Override this method to add your custom logic there
     */
    init: function () {
      console.log('vao day')
        },
    _renderView: function () {
      var self = this;

      // call to parent to continue original rendering
      return this._super.apply(this, arguments).then(function () {

        // Your custom logic after rendering goes here
        // Use something like this to get row values
        // sum of quantity should be available in dataset
        // or can be calculated from dataset of each row
        console.log('a du')
        self.$el.find('.o_list_view').each(function () {
          var quantitySum = 0;
          $(this).find('.o_list_record').each(function () {
            var quantity = parseFloat($(this).find("td:contains('quantity')").text());
            quantitySum += quantity;
          });

          // Now you can do anything with the calculated sum,
          // For example, add to the specific field

        });

      });
    },

  });
});