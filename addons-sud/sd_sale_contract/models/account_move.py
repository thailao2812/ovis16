# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
    
class AccountInvoice(models.Model):
    _inherit = "account.move"
    
    sale_contract_id = fields.Many2one('sale.contract', string='Sale Contract', readonly=True, states={'draft': [('readonly', False)]}, ondelete='cascade')

    