
# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
import math
from datetime import datetime, date, timedelta
import math


class PurchaseContract(models.Model):
    _inherit = 'purchase.contract'

    code_partner = fields.Char(string='Partner Code', related='partner_id.partner_code', store=True)
    stop_loss_price = fields.Float(string='Stop Loss %')
    date_fix_for_advance = fields.Integer(string='Time Fix')

    note_by_security_gate = fields.Text(string='Note Security Gate')

    @api.depends('request_payment_ids', 'request_payment_ids.type', 'type',
                 'request_payment_ids.type_of_ptbf_payment', 'request_payment_ids.request_amount')
    def _compute_advance_amount(self):
        for line in self:
            amount = 0.0
            if line.type == 'ptbf':
                for i in line.request_payment_ids:
                    if i.type_of_ptbf_payment == 'advance':
                        amount += i.request_amount or 0.0
                line.advance_amount = amount