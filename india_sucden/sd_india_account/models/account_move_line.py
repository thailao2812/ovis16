# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError, AccessError, RedirectWarning
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
import math


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    price_unit = fields.Float(digits=(12,4))