# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class SaleContractLine(models.Model):
    _inherit = "sale.contract.line"

    no_of_bags = fields.Float(string='No of bag',digits=(12, 0), readonly=False, compute='_compute_bags', store=True)


    @api.depends('product_qty', 'packing_id', 'packing_id.capacity')
    def _compute_bags(self):
        for record in self:
            if record.packing_id:
                if record.packing_id.capacity > 0:
                    record.no_of_bags = record.product_qty / record.packing_id.capacity
                else:
                    record.no_of_bags = 0


class SaleContract(models.Model):
    _inherit = "sale.contract"

    no_of_bags = fields.Float(string='No of bag', digits=(12, 0), related='contract_line.no_of_bags', store=True)

    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=True, readonly=True,
                                   states={'draft': [('readonly', False)]}, default=False)
