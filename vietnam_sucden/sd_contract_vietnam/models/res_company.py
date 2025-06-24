# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from num2words import num2words

class ResCompany(models.Model):
    _inherit = 'res.company'

    stock_account_coffee_id = fields.Many2one(
        'account.account', 'Intermediary account Coffee',
        help="""When automated inventory valuation is enabled on a product, this account will hold the current value of the products.""", )

    stock_account_consumable_id = fields.Many2one(
        'account.account', 'Intermediary account Consumable',
        help="""When automated inventory valuation is enabled on a product, this account will hold the current value of the products.""", )