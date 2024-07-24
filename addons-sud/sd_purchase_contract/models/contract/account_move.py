# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"

class AccountMove(models.Model):
    _inherit = "account.move" 

    def _total_qty(self):
        for order in self:
            total_qty = 0
            for line in order.invoice_line_ids:
                total_qty +=line.quantity
            order.total_qty = total_qty
            
    total_qty = fields.Float(compute='_total_qty', string = 'Total Qty', digits=(12, 2))
    
    purchase_contract_id = fields.Many2one('purchase.contract', string='Purchase Contract')
    contract_id = fields.Many2one('purchase.contract',string="NVP Contract")
    
    supplier_inv_date=fields.Date('Vendor Invoice Date', readonly=True, states={'draft':[('readonly',False)]}, copy=False)