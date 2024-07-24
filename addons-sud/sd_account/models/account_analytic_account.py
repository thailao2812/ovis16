# -*- coding: utf-8 -*-
from odoo import api, Command, fields, models, _
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from odoo.addons.base.models.res_bank import sanitize_account_number
from odoo.tools import remove_accents
import logging
import re

class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"
    
    parent_id = fields.Many2one('account.analytic.account', string='Parent Analytic Account')
                   
    child_ids = fields.One2many('account.analytic.account', 'parent_id', string='Child Accounts')
    
    
    analytic_type = fields.Selection([
            ('1','Controlling Area'),
            ('2','Company Code'),
            ('3','Division'),
            ('4','Cost Group'),
            ('5','Cost Center'),
            ('6','Profit Center'),
    ], string='Analytic Type', default='5')