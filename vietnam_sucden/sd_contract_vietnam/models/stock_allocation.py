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

    fot_name = fields.Char(string='GRN FOT', related='picking_id.description_name', store=True)

    description = fields.Char(string='GRN', related='picking_fot_id.name', store=True)

    picking_fot_id = fields.Many2one('stock.picking', string='GRN FOT')

    @api.onchange('picking_fot_id')
    def onchange_stock_picking(self):
        for rec in self:
            if rec.picking_fot_id:
                rec.picking_id = rec.picking_fot_id.id
