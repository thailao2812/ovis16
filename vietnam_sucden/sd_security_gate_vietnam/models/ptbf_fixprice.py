DATE_FORMAT = "%d-%m-%Y"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError


class PTBFFixPrice(models.Model):
    _inherit = 'ptbf.fixprice'

    request_payment_ids = fields.One2many('request.payment', 'price_tobe_fix', ondelete='cascade')
    remain_qty = fields.Float(compute='_compute_remain_qty', string='Remaining Quantity', store=True)

    @api.depends('request_payment_ids', 'request_payment_ids.state', 'request_payment_ids.payment_quantity', 'quantity')
    def _compute_remain_qty(self):
        for rec in self:
            rec.remain_qty = rec.quantity - sum(rec.request_payment_ids.mapped('payment_quantity'))

    def name_get(self):
        result = []
        for rec in self:
            if rec.no and rec.date_fix:
                name = "No " + rec.no + " Date: " + rec.date_fix.strftime(DATE_FORMAT)
                result.append((rec.id, name))
        return result