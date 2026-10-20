# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import UserError


class MarkupValue(models.Model):
    _name = 'markup.value'
    _description = 'Markup Value'

    name = fields.Char(string='Name', required=True)
    from_date = fields.Date(string='From Date', required=True)
    to_date = fields.Date(string='To Date', required=True)
    value = fields.Float(string='Value in $', required=True)