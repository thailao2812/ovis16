# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class SaleContractLine(models.Model):
    _inherit = "sale.contract.line"

    no_of_bags = fields.Float(string='No of bag',digits=(12, 0), readonly=False, compute='_compute_bags', store=True)
    price_unit = fields.Float(compute='_final_price', digits=(16, 2),store=True,string="Price")

    @api.depends('final_g2_price', 'premium', 'final_g2_diff', 'premium_adjustment')
    def _final_price(self):
        for sale in self:
            sale.price_unit = 0

    @api.depends('product_qty', 'price_unit', 'tax_id', 'contract_id.type', 'conversion')
    def _compute_amount(self):
        for line in self:
            conversion = line.conversion
            if line.contract_id.type == 'local':
                conversion = 1
            price = line.price_unit / conversion
            taxes = line.tax_id.compute_all(price, line.contract_id.currency_id, line.product_qty,
                                            product=line.product_id, partner=line.contract_id.partner_id)
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

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
