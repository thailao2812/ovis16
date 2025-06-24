# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from datetime import datetime, date, timedelta


class AccountMove(models.Model):
    _inherit = 'account.move'

    request_payment_invoice_ids = fields.One2many('request.payment.invoice', 'invoice_id', string='Request Payment Invoice')