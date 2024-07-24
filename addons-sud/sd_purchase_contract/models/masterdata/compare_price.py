# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class ComparePrice(models.Model):
    _name = 'compare.price'

    mkt = fields.Char(string="Mkt")
    ice_eu = fields.Float(string='ICE EU')
    g2_replacement = fields.Float(string='G2 Replacement')
    faq_price = fields.Float(string='FAQ Price')
    fob_price = fields.Float(string='FOB Price')
    grade_price = fields.Float(string='Grade Price')