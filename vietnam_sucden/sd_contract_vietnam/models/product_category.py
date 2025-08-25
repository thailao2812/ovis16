# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class ProductCategory(models.Model):
    _inherit = 'product.category'

    property_account_expense_categ_id = fields.Many2one(domain=[])
