# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class AccountTax(models.Model):
    _inherit = 'account.tax'

    default = fields.Boolean(string='Default')