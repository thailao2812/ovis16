# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class PurchaseContract(models.Model):
    _inherit = 'purchase.contract'

    list_farmer = fields.One2many('list.farmer', 'purchase_contract_id')

    equiv_faq_price = fields.Float(string='Equiv. FAQ price', related='contract_line.equiv_faq_price', store=True)

    deposit_amount = fields.Float(string='Deposit Amount')

    print_company = fields.Boolean(string='Print Company Name')

    open_qty = fields.Float(string='No Payment Qty')

    list_open_qty = fields.One2many('open.qty.npe', 'purchase_contract_id')

    user_approve = fields.Many2one('res.users', string='User Approve', readonly=False, domain=[('trader', '=', True)])

    percent_advance_price = fields.Integer(string="Percent Advance Price", default=70)


class OpenQtyNPE(models.Model):
    _name = 'open.qty.npe'

    purchase_contract_id = fields.Many2one('purchase.contract')
    contract_id = fields.Many2one('purchase.contract', string='NPE')
    qty = fields.Float(string='')
