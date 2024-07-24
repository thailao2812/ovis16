# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class StockLot(models.Model):
    _inherit = 'stock.lot'

    p_qty = fields.Float(string="Ctr.Qty (Kg)", related='p_contract_id.p_qty', store=True)