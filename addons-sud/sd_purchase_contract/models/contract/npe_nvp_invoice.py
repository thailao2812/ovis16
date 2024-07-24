# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

    
class NpeNvpInvoice(models.Model):
    _name = "npe.nvp.invoice"
    _order = 'id desc'
    
    contract_id = fields.Many2one('purchase.contract', string="Contract")
    invoice_id = fields.Many2one('account.move', string="invoice")
    product_qty = fields.Float(related='invoice_id.total_qty', readonly=True)
    amount_total = fields.Monetary(related='invoice_id.amount_total',string="Amount Total", readonly=True)
    npe_id = fields.Many2one('purchase.contract',string="NPE")
    currency_id =fields.Many2one(related='invoice_id.currency_id', string="Currency")