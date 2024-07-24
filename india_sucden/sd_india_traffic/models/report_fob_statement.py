# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError


class ReportFOBStatement(models.Model):
    _name = 'report.fob.statement'
    _description = 'Report FOB Statement'

    product_id = fields.Many2one('product.product', string='Item Group')
    item_id = fields.Many2one('product.group', string='Item Group')
    p_number = fields.Many2one('sale.contract.india', string='PSC No.')
    p_date = fields.Date(string='PSC Date')
    sn_no = fields.Char(string='SN No')
    sn_date = fields.Date(string='SN Date')
    purchase_contract = fields.Many2one('purchase.contract', string='PC No.')
    pc_date = fields.Date(string='PC Date')
    no_of_bag = fields.Float(string='No Of Bags')
    pc_qty = fields.Float(string='PC Qty')
    outturn = fields.Float(string='Outturn %')
    green_coffee = fields.Float(string='Green Coffee (Kgs)')
    fob_value = fields.Float(string='FOB Value')
    currency_uom = fields.Char(string='Currency / UOM')
    value_usd = fields.Float(string='Value (USD)')
    forex = fields.Float(string='Forex')
    farm_gate = fields.Float(string='Farm Gate Price Per 50kg (INR)')
    sale_value = fields.Float(string='Sale Value (INR)')
    value_raw_coffee = fields.Float(string='Value Raw Coffee (INR)')
    margin_value = fields.Float(string='Margin Value(INR)')
    margin_per_mt = fields.Float(string='Margin Per MT (INR)')
    market_price = fields.Float(string='Market Price')
    currency_uom_fob = fields.Char(string='Currency / UOM')
    contract_price = fields.Float(string='Contract Price')
    currency_uom_2nd = fields.Char(string='Currency / UOM')
    differential = fields.Float(string='Differential')
