# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict
DATE_FORMAT = "%Y-%m-%d"

class StockReport(models.Model):
    _name = 'stock.report'
    _description = 'Stock Report'

    stack_id = fields.Many2one('stock.lot', string='Stack No.')
    zone_id = fields.Many2one('stock.zone', string='Zone', related='stack_id.zone_id', store=True)
    packing_id = fields.Many2one('ned.packing', string='Packing', related='stack_id.packing_id', store=True)
    building_id = fields.Many2one('building.warehouse', string='Building', related='stack_id.building_id', store=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', related='stack_id.warehouse_id', store=True)
    product_id = fields.Many2one('product.product', related='stack_id.product_id', string='Product', store=True)
    init_qty = fields.Float(string='Balance Net', digits=(12, 2))

    @api.model
    def cron_action_create_stock_report(self):
        # self.env['stock.report'].search([]).unlink()
        for lot in self.env['stock.lot'].search([
            ('init_qty', '>', 0)
        ]):
            self.env['stock.report'].create({
                'stack_id': lot.id,
                'init_qty': lot.init_qty,
            })