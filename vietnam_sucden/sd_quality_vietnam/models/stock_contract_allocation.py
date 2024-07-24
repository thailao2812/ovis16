# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _, tools
import time
from datetime import timedelta
from odoo.exceptions import UserError, ValidationError


class StockContractAllocation(models.Model):
    _inherit = 'stock.contract.allocation'

    note = fields.Char(string='Note')
    sample_lot = fields.Char(string='Sample Lot')