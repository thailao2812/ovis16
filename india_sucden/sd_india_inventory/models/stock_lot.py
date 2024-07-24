# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID


class StockLot(models.Model):
    _inherit = 'stock.lot'

    building_id = fields.Many2one('building.warehouse', string='Building')
    adj_qty = fields.Float(string='Adjustment Qty', compute='compute_adjustment_qty', store=True, digits=(16, 0))

    @api.depends('move_line_ids', 'move_line_ids.state', 'move_line_ids.picking_id')
    def compute_adjustment_qty(self):
        for rec in self:
            if rec.move_line_ids.filtered(lambda x: x.picking_id.picking_type_id.code == 'phys_adj' and x.state == 'done'):
                rec.adj_qty = sum(rec.move_line_ids.filtered(lambda x: x.picking_id.picking_type_id.code == 'phys_adj' and x.state == 'done').mapped('init_qty'))
            else:
                rec.adj_qty = 0