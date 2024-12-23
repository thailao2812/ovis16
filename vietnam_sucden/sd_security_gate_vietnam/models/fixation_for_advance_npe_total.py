# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from odoo.tools import float_round


class FixationAdvancePTBFNPETotal(models.Model):
    _name = 'fixation.advance.ptbf.npe.total'

    request_payment_id = fields.Many2one('request.payment', string='Request Payment', ondelete='cascade')
    request_origin_id = fields.Many2one('request.payment', string='Request Origin', ondelete='cascade')
    name = fields.Char(string='Advance Payment')
    contract_id = fields.Many2one('purchase.contract', string='NPE No.')
    date_contract = fields.Date(string='Date Advance')
    temp_quantity = fields.Integer(string='Quantity')
    quantity = fields.Integer(string='Quantity')
    request_amount = fields.Float(string='Request Amount', digits=(12, 0))
    usd = fields.Float(string='USD', compute='_compute_usd', store=True)
    ex_rate = fields.Float(string='Exchange Rate', digits=(12, 0))
    rate = fields.Float(string='Rate', digits=(12, 2))
    interest = fields.Float(string='Interest', digits=(12, 0))
    vnd = fields.Float(string='VND', digits=(12, 0))
    total = fields.Float(string='Total', digits=(12, 0))

    check = fields.Boolean(string='Check', compute='_compute_check', store=True)

    @api.depends('name')
    def _compute_check(self):
        for rec in self:
            if rec.name == 'Total':
                rec.check = True
            else:
                rec.check = False