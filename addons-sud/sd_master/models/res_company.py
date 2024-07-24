# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

class ResCompany(models.Model):
    _inherit = "res.company"
    
    second_currency_id = fields.Many2one('res.currency', string='Second Currency')
    
    #2 tài khoản định nghĩa bút toán kết chuyễn lãi
    incomce_from_advance_payment_id = fields.Many2one('account.account', string='Income From Advance Payment')
    interest_income_shipment_id = fields.Many2one('account.account', string='Interest income shipment')
    
    fax = fields.Char(string="Fax")