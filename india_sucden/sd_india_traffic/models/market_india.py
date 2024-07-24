# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID


class MarketIndia(models.Model):
    _name = 'market.india'
    _inherit = ['mail.thread']
    _description = 'Market'

    name = fields.Char(string='Location')
    rate = fields.Float(string='Rate', digits=(12, 5))
