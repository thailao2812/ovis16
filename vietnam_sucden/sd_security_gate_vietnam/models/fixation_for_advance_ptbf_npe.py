# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from odoo.tools import float_round


class FixationAdvancePTBFNPE(models.Model):
    _name = 'fixation.advance.ptbf.npe'

    request_payment_id = fields.Many2one('request.payment', string='Request Payment', ondelete='cascade')
    request_origin_id = fields.Many2one('request.payment', string='Request Origin', ondelete='cascade')
    name = fields.Char(string='Advance Payment')
    contract_id = fields.Many2one('purchase.contract', string='NPE No.')
    date_contract = fields.Date(string='Date Advance')
    temp_quantity = fields.Integer(string='Quantity')
    quantity = fields.Integer(string='Quantity')
    request_amount = fields.Float(string='Request Amount', digits=(12, 0))
    usd = fields.Float(string='USD', compute='_compute_usd', store=True, digits=(12, 6))
    ex_rate = fields.Float(string='Exchange Rate', digits=(12, 0))
    rate = fields.Float(string='Rate', digits=(12, 2))
    interest = fields.Float(string='Interest', digits=(12, 0))
    vnd = fields.Float(string='VND', digits=(12, 6), compute='_compute_total', store=True)
    total = fields.Float(string='Total', digits=(12, 6), compute='_compute_total', store=True)

    check = fields.Boolean(string='Check', compute='_compute_check', store=True)

    @api.depends('usd', 'ex_rate', 'interest', 'vnd')
    def _compute_total(self):
        for rec in self:
            if rec.name == 'Còn lại/ Remain Payment:':
                rec.vnd = rec.usd * rec.ex_rate
                # total_interest = rec.request_payment_id.total_interest_advance_ptbf_npe
                # print(total_interest, 'total_interest')
                # print(rec.vnd, 'vnd')
                rec.total = rec.usd * rec.ex_rate
            if rec.name == 'Total':
                rec.total = rec.vnd + rec.interest

    @api.depends('name')
    def _compute_check(self):
        for rec in self:
            rec.check = False

    @api.depends('total', 'ex_rate')
    def _compute_usd(self):
        for rec in self:
            if rec.name == 'Total':
                if rec.ex_rate > 0:
                    rec.usd = float_round(rec.total / rec.ex_rate, precision_digits=6)
                else:
                    rec.usd = 0

    def unlink(self):
        for rec in self:
            request_origin = rec.request_origin_id
            if rec.name == 'Total':
                request_origin.mirror_request_amount += rec.quantity
        return super(FixationAdvancePTBFNPE, self).unlink()