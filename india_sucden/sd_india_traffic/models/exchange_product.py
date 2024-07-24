# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID


class ExchangeProduct(models.Model):
    _name = 'exchange.product.india'
    _inherit = ['mail.thread']

    name = fields.Char(string='Exchange Product')
    default_data = fields.Selection([
        ('no', 'No'),
        ('yes', 'Yes')
    ], string='Default', default='no')
    active = fields.Boolean(string='Active')