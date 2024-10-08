# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class ContractPricePurchase(models.Model):
    _name = "contract.price.purchase"

    name = fields.Char(string='Reference')
    product_id = fields.Many2one('product.product', string='Item name', related='contract_id.product_id', store=True)
    date_price = fields.Date(string='Date', related='contract_id.date_order', store=True)
    exchange = fields.Many2one('exchange.india', string='Exchange')
    exchange_rate = fields.Float(string='Exchange Rate', digits=(12, 2))
    fob = fields.Float(string='FOB', digits=(12, 2))
    a_differential = fields.Float(string='A Differential', digits=(12, 2))
    ab_differential = fields.Float(string='AB Differential', digits=(12, 2))
    grade_differential = fields.Float(string='Grade Differential', digits=(12, 2))

    partner_id = fields.Many2one('res.partner', string='Supplier Name', related='contract_id.partner_id', store=True)
    contract_number = fields.Char(string='Contract')
    price = fields.Float(string='Price', digits=(12, 2), related='contract_id.relation_price_unit', store=True)
    premium = fields.Float(string='Premium Amount', digits=(12, 2), related='contract_id.premium', store=True)
    currency_id = fields.Many2one('res.currency', related='contract_id.currency_id', store=True)
    total = fields.Float(string='Total Contract Price', digits=(12, 2), compute='compute_total', store=True)
    quantity = fields.Float(string='Quantity', related='contract_id.total_qty', store=True)
    certificate_id = fields.Many2one('ned.certificate', string='Certificate', related='contract_id.certificate_id', store=True)
    market_price = fields.Float(string='Market Price')

    # new field
    contract_id = fields.Many2one('purchase.contract', string='Contract')
    trade_month = fields.Many2one('s.period', string='Trade Month')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approve', 'Approved'),
    ], string='State', default='draft')
    outturn = fields.Float(string='Outturn %')

    @api.depends('price', 'premium')
    def compute_total(self):
        for rec in self:
            rec.total = rec.price + rec.premium

    def action_approve(self):
        for rec in self:
            rec.state = 'approve'

    def action_set_to_draft(self):
        for rec in self:
            rec.state = 'draft'