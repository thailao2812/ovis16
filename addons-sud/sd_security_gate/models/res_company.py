# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

class res_company(models.Model):
    _inherit = 'res.company'
    
    time_to_reject_the_goods = fields.Integer(string='Time To Reject The Goods')