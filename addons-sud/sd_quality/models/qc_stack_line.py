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


class QCStackLine(models.Model):
    _name = 'qc.stack.line'

    product_id = fields.Many2one('product.product', string='Product')
    allocation_id = fields.Many2one('sale.contract', 'Allocation Ref')
    wr_id = fields.Many2one('stock.lot', string='WR')
    mc = fields.Float(string="MC", digits=(12, 2))
    fm = fields.Float(string="Fm", digits=(12, 2))
    black = fields.Float(string="Black", digits=(12, 2))
    broken = fields.Float(string="Broken", digits=(12, 2))
    screen13 = fields.Float(string="Screen13", digits=(12, 2))
    screen16 = fields.Float(string="Screen16", digits=(12, 2))
    screen18 = fields.Float(string="Screen18", digits=(12, 2))
    instored = fields.Float(string="In Weight", digits=(12, 2))
    exstored = fields.Float(string="Ex Weight", digits=(12, 2))
    doc_weight = fields.Float(string='Docs Weight', digits=(12, 2))  
    