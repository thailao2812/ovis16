# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

from datetime import datetime
import time
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%d-%m-%Y"

    
class InvoicedAllocation(models.Model):
    _name = "invoiced.allocation"

                    
    contract_id = fields.Many2one('purchase.contract', string='Contract')
    account_id = fields.Many2one('account.move', string='Invoiced')
    currency_id = fields.Many2one(related='account_id.currency_id',string='Currency')
    amount_total = fields.Monetary(related='account_id.amount_total',string='Amount Total',digits=(12, 0))
    price_unit = fields.Float(related='account_id.invoice_line_ids.price_unit',string='Price Unit',digits=(12, 0))
    qty_invoiced = fields.Float(related='account_id.total_qty',string='Qty Invoiced',digits=(12, 0))
    qty_contract = fields.Float(related='contract_id.total_qty',string='Qty Contract',digits=(12, 0))
    date_contract = fields.Date(related='contract_id.date_order',string='Date Contract')
    state = fields.Selection([('draft', 'New'), ('approved', 'Approved')], string='Status',
                             readonly=True, copy=False, index=True, default='draft')
    qty_allocation = fields.Float(string='Qty Allocation',digits=(12, 0))
    value_allocation = fields.Float(string = 'Values Allocation',digits=(12, 0))
    
    

    def button_approved(self):
        self.contract_id.qty_invoiced_received = self.contract_id.qty_invoiced_received + self.qty_allocation
        self.write({'state': 'approved'})
    
    def cancel_allocation(self):
        self.contract_id.qty_invoiced_received = self.contract_id.qty_invoiced_received - self.qty_allocation
        self.write({'state': 'draft'})