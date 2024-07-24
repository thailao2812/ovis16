# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

from datetime import datetime
import time
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
#

class StockContractAllocation(models.Model):
	_name = "stock.contract.allocation"

	allocation_date = fields.Datetime(string='Date')
	stack_no = fields.Many2one('stock.lot', string='Stack')
	zone_id = fields.Many2one('stock.zone',related='stack_no.zone_id', string='Zone',store =True)
	stock_balance = fields.Float(related='stack_no.init_qty', string='Stock Balance',store =True)
	product_name = fields.Many2one('product.product',related='stack_no.product_id', string='Product Name', store= True)
	shipping_id = fields.Many2one('shipping.instruction', string='SI no.',)
	factory_etd = fields.Date(related='shipping_id.factory_etd', string='Factory Etd', store= True)
	partner_id = fields.Many2one('res.partner', related='shipping_id.partner_id', string="Customer",store =True)
	allocating_quantity = fields.Float(string='Allocating quantity')
	packing_type = fields.Many2one('ned.packing',related='stack_no.packing_id', string='Packing Type')
	allocation_availabibity = fields.Float(compute="_compute_allocation_availability", string="Allocation Availabibity", store = True)
	grade_name = fields.Char(string='Group by Grade', related='stack_no.product_id.categ_id.name', store=True)
    
    
	def load_stack_info(self):
		if self.id:
			self.allocating_quantity = self.stack_no.init_qty
			# self.packing_type = self.stack_no.packing_id
			# self.product_id = self.shipping_id.product_id
			# self.write(val)
		return True
	
	@api.depends('shipping_id')
	def _compute_allocation_availability(self):
		allocated = 0
		available = 0
  # for r in self:
  # 	if r.shipping_id.id == self.shipping_id.id:
  # 		allocated = allocated + r.shipping_id.allocating_quantity
  # 	available = r.stack_no.init_qty - allocated
		return available

	def load_availability(self):
		allocated = 0
		for r in self:
			if r.shipping_id == self.shipping_id:
				allocated = allocated + r.shipping_id.allocating_quantity
			available = r.stack_no.init_qty - allocated
			r.allocation_availabibity = available
		
		
		