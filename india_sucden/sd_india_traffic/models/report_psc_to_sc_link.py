# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError


class ReportPSCtoSCLink(models.Model):
    _name = 'report.psc.sc.link'
    _description = 'Report PSC to SC Linked'

    p_number = fields.Many2one('sale.contract.india', string='P Contract No')
    p_qty = fields.Float(string='P Contract Qty Mt')
    p_price = fields.Float(string='P Contract price')
    currency_uom = fields.Char(string='Currency / UOM', default='USD/MT')
    p_amount = fields.Float(string='P Contract Total Amount')
    shipping_instruction_id = fields.Many2one('shipping.instruction', string='SI No')
    s_contract_id = fields.Many2one('s.contract', string='SC No')
    product_id = fields.Many2one('product.product', string='Product Name')
    s_qty = fields.Float(string='SC Qty')
    allocated_qty = fields.Float(string='Allocated Qty')
    differential = fields.Float(string='Differential')
    packing_cost = fields.Float(string='Packing Cost')
    certificate_premium = fields.Float(string='Certificate Premium')
    s_total_price = fields.Float(string='S Contract Total Price')
    currency_uom_2nd = fields.Char(string='Currency / UOM', default='USD/MT')
    s_contract_amount = fields.Float(string='S Contract Amount')
    currency_uom_3rd = fields.Char(string='Currency / UOM', default='USD/MT')
    open_position = fields.Float(string='Open Position Qty')
    open_position_value = fields.Float(string='Open Position Value')
