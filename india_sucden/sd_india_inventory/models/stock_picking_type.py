# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    bag_transfer = fields.Boolean(string='Bag Transfer', default=False)

