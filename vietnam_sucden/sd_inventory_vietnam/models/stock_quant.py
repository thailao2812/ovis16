# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
import time
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import timedelta, datetime, date


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.constrains('location_id')
    def check_location_id(self):
        return True
