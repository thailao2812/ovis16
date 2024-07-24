# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
import time
import math


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    sup_product_id = fields.Many2one('product.product', string='Sub Product')

    def custom_round(self, number: float) -> int:
        if number - round(number) == 0.5:
            return math.ceil(number)
        else:
            return round(number)

    @api.onchange('first_weight', 'second_weight', 'packing_id', 'bag_no', 'tare_weight')
    def onchange_weight(self):
        if not self.packing_id:
            tare_weight = 0.0
            net_weight = (self.first_weight or 0.0) - (self.second_weight or 0.0) - tare_weight
            if net_weight:
                self.update({'tare_weight': tare_weight, 'init_qty': net_weight, 'qty_done': net_weight})
        else:
            tare_weight = self.packing_id.tare_weight or 0.0
            tare_weight = self.bag_no * tare_weight
            tare_weight = self.custom_round(tare_weight)
            net_weight = (self.first_weight or 0.0) - (self.second_weight or 0.0) - tare_weight
            if net_weight:
                self.update({'tare_weight': tare_weight, 'init_qty': net_weight, 'qty_done': net_weight})