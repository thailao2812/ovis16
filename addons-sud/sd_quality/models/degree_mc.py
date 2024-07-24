# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class DegreeMc(models.Model):
    _name = 'degree.mc'
    _order = 'id desc'
    
    mconkett = fields.Float(digits=(12, 2),string="MConKett")
    deduction = fields.Float(digits=(12, 2),string="Deduction")

    
    