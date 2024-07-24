# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from datetime import timedelta
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
import time
from datetime import date
from datetime import datetime

from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT 
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
                
from lxml import etree



class SContract(models.Model):
    _inherit = "s.contract"

    wr_line = fields.Many2one('stock.lot', string='Stack')
    wr_line_code = fields.Char(related='wr_line.code', string='WR', store = True)
    init_qty = fields.Float(related='wr_line.init_qty', string='In Weight', digits=(12, 0))
    out_qty = fields.Float(related='wr_line.out_qty', string='Out Weight', digits=(12, 0))
    remaining_qty = fields.Float(related='wr_line.remaining_qty', string='Balance Weight', digits=(12, 0))


