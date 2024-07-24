odoo.define('besco_stock.stock_barcode_menu_inherit', function (require) {
'use strict';

	var AbstractAction = require('web.AbstractAction');
	var core = require('web.core');
	var Dialog = require('web.Dialog');
	var Session = require('web.session');
	var StockBarcodeMenu = require('stock_barcode.MainMenu');
	
	var _t = core._t;

	StockBarcodeMenu.MainMenu.include({
		
		events: {
	        "click .button_operations": function(){
	            this.do_action('stock_barcode.stock_picking_type_action_kanban');
	        },
	        "click .button_inventory": function(){
	        	this.do_action('besco_stock.stock_inventory_action_kanban');
	        },
	        "click .o_stock_barcode_menu": function(){
	            this.trigger_up('toggle_fullscreen');
	            this.trigger_up('show_home_menu');
	        },
	    },
		
	});
	
});
