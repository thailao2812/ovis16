# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class ConvertedLine(models.Model):
    _name = 'converted.line'

    request_payment_id = fields.Many2one('request.payment', ondelete='cascade')
    request_origin_id = fields.Many2one('request.payment', ondelete='cascade')
    seq = fields.Integer(string='No')
    fixation_qty = fields.Float(string='Fixation Quantity')
    purchase_contract_id = fields.Many2one('purchase.contract', string='Contract No')
    fixation_price = fields.Float(string='Provisional')
    advance_payment = fields.Float(string='Advanced Payment')
    advance_date = fields.Date(string='Advanced Date')
    interest_rate = fields.Float(string='Interest rate/Date', digits=(16, 6))
    total_days = fields.Integer(string='Total Days')
    interest = fields.Float(string='Interest')

    def unlink(self):
        for rec in self:
            request_origin = rec.request_origin_id
            request_origin.mirror_request_amount += rec.fixation_qty
        return super(ConvertedLine, self).unlink()
