# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

class StockZone(models.Model):
    _inherit = "stock.zone"
    
    area_name = fields.Char(string='Area', required=True)