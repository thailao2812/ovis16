# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    transaction_no = fields.Char(string='Transaction No.', related='production_id.transaction_no', store=True)
    picking_grn_id = fields.Many2one('stock.picking', string='GRN Allocated')