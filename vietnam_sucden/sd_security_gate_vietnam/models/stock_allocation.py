# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

from datetime import datetime
import time

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%d-%m-%Y"
DAT = "%Y-%m-%d"


class StockAllocation(models.Model):
    _inherit = "stock.allocation"

    grn_fa_id = fields.Many2one('stock.picking', string='GRN FA', related='picking_id.link_backorder_id', store=True)