# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class PurchaseContractInvoice(models.Model):
    _name = 'purchase.contract.invoice'

    move_id = fields.Many2one('account.move', string='Invoice')
    purchase_contract_id = fields.Many2one('purchase.contract', string='Purchase Contract')
    date = fields.Date(string='Date')
    quantity = fields.Float(string='Quantity')
    amount_allocated_untaxed = fields.Float(string='Amount Allocated (Untaxed)')
    amount_allocated_tax = fields.Float(string='Amount Allocated (Tax)')
    amount_allocated_total = fields.Float(string='Amount Allocated (Total)')