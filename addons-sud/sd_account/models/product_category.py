# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class ProductCategory(models.Model):
    _inherit = 'product.category'
    
    
    property_stock_account_revenue_local = fields.Many2one('account.account', string="Stock Revenue local")
