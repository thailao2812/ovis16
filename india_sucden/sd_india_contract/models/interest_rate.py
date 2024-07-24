# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class InterestRate(models.Model):
    _inherit = "interest.rate"

    provisional_rate = fields.Float(string='Interest Temporary', compute=False, digits=(12, 0))