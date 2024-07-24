# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID


class FixedCost(models.Model):
    _name = 'fixed.cost.india'
    _inherit = ['mail.thread']

    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date to')
    fixed_cost = fields.Float(string='Fixed Cost/MT', tracking=True)