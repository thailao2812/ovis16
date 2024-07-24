# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID


class ItemGroupIndia(models.Model):
    _name = 'product.group'
    _inherit = ['mail.thread']
    _description = 'Item Group'

    name = fields.Char(string='Item Group')
