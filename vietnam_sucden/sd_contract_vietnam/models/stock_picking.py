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


class StockPicking(models.Model):
    _inherit = "stock.picking"

    invoice_allocate_ids = fields.One2many('stock.picking.allocated', 'picking_id', string='Invoice Allocate')
    allocated_invoice_amount = fields.Integer(string='Allocated Invoice Amount', compute='_compute_allocated_invoice_amount', store=True)

    @api.depends('invoice_allocate_ids', 'invoice_allocate_ids.allocated_amount')
    def _compute_allocated_invoice_amount(self):
        for rec in self:
            rec.allocated_invoice_amount = sum(rec.invoice_allocate_ids.mapped('allocated_amount'))
