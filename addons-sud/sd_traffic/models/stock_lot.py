# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError


class StockLot(models.Model):
    _inherit = 'stock.lot'

    bag_in = fields.Float(string='Bags In', compute='compute_bags_in', store=True)

    @api.depends('move_line_ids', 'move_line_ids.picking_id', 'move_line_ids.picking_id.state', 'move_line_ids.state')
    def compute_bags_in(self):
        for record in self:
            bag_in = 0
            for line in record.move_line_ids:
                if line.picking_id.picking_type_id.code in ('production_in', 'transfer_in', 'incoming', 'phys_adj'):
                    if line.state != 'done':
                        continue
                    bag_in += line.bag_no
            record.bag_in = bag_in