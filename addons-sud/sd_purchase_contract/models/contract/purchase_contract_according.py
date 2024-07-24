# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"

class PurchaseContractAccording(models.Model):
    _name = "purchase.contract.according"

    name = fields.Char(string='Name by English', size=256)
    name_vn = fields.Char(string='Name by VN', size=256)
    eposition = fields.Char(string='Position by English', size=256)
    vnposition = fields.Char(string='Position by VN', size=256)
    number = fields.Char(string='Number', size=256)
    appr_date = fields.Date(string='Approved Date')