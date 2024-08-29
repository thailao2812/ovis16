# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class ReferenceInformation(models.Model):
    _name = 'reference.information'

    request_id = fields.Many2one('request.payment')
    request_payment_id = fields.Many2one('request.payment', string='Request Payment')
    name = fields.Char(string='Description')
    request_date = fields.Date(string='Date', related='request_payment_id.date', store=True, readonly=False)
    total_advance_payment_usd = fields.Float(string='Total Advance Payment (USD)', digits=(12, 2), related='request_payment_id.total_advance_payment_usd', store=True, readonly=False)
    rate = fields.Float(string='Exchange Rate', digits=(12, 0), related='request_payment_id.rate', store=True, readonly=False)
    request_amount = fields.Float(string='Request Amount VND', digits=(12, 0), related='request_payment_id.request_amount', store=True, readonly=False)