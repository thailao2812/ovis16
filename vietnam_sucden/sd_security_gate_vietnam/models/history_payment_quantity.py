# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class HistoryPaymentQuantity(models.Model):
    _name = 'history.payment.quantity'

    request_payment_id = fields.Many2one('request.payment', string='Request Payment', ondelete='cascade')
    name = fields.Char(string='Times')
    quantity_char = fields.Char(string='Quantity')
    quantity = fields.Float(string='Quantity', digits=(12, 0))
    
