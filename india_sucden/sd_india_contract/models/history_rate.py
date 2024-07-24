# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class HistoryRate(models.Model):
    _inherit = "history.rate"

    final_price_en = fields.Float(string="Final Price")
    total_amount_vn = fields.Float(string="Total Amount")