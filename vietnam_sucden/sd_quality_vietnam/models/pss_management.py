# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

class PssManagement(models.Model):
    _inherit="pss.management"
    
    license_id = fields.Char(related='shipping_id.license_list', string='License', store=True)
