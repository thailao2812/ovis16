odoo.define('besco_stock.picking_client_action_inherit', function (require) {
'use strict';

	var core = require('web.core');
	var ClientAction = require('stock_barcode.ClientAction');
	var ViewsWidget = require('stock_barcode.ViewsWidget');
	var PickingClientAction = require('stock_barcode.picking_client_action');
	
	var _t = core._t;

	PickingClientAction.include({
		
		_makeNewLine: function (product, barcode, qty_done, package_id, result_package_id) {
			var virtualId = this._getNewVirtualId();
	        var currentPage = this.pages[this.currentPageIndex];
	        var newLine = {
	            'picking_id': this.currentState.id,
	            'product_id': {
	                'id': product.id,
	                'display_name': product.display_name,
	                'barcode': barcode,
	                'tracking': product.tracking,
	            },
	            'product_barcode': barcode,
	            'display_name': product.display_name,
	            'product_uom_qty': 0,
	            'product_uom_id': product.uom_id,
	            'qty_done': qty_done,
	            'location_id': {
	                'id': currentPage.location_id,
	                'display_name': currentPage.location_name,
	            },
	            'location_dest_id': {
	                'id': currentPage.location_dest_id,
	                'display_name': currentPage.location_dest_name,
	            },
	            'package_id': package_id,
	            'result_package_id': result_package_id,
	            'state': 'assigned',
	            'reference': this.name,
	            'virtual_id': virtualId,
	        };
	        return newLine;
		},
		
	});
	
});
