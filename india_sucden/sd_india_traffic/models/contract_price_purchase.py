# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class ContractPricePurchase(models.Model):
    _name = "contract.price.purchase"

    name = fields.Char(string='Reference')
    product_id = fields.Many2one('product.product', string='Item name')
    date_price = fields.Date(string='Date')
    exchange = fields.Many2one('exchange.india', string='Exchange')
    exchange_rate = fields.Float(string='Exchange Rate', digits=(12, 2))
    fob = fields.Float(string='FOB', digits=(12, 2))
    a_differential = fields.Float(string='A Differential', digits=(12, 2))
    ab_differential = fields.Float(string='AB Differential', digits=(12, 2))
    grade_differential = fields.Float(string='Grade Differential', digits=(12, 2))

    partner_id = fields.Many2one('res.partner', string='Supplier Name')
    contract_number = fields.Char(string='Contract')
    price = fields.Float(string='Price', digits=(12, 2))
    premium = fields.Float(string='Premium Amount', digits=(12, 2))
    total = fields.Float(string='Total Contract Price', digits=(12, 2), compute='compute_total', store=True)
    quantity = fields.Float(string='Quantity')
    certificate_id = fields.Many2one('ned.certificate', string='Certificate')
    market_price = fields.Float(string='Market Price')

    @api.depends('price', 'premium')
    def compute_total(self):
        for rec in self:
            rec.total = rec.price + rec.premium