# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import UserError

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class ContractPricePurchase(models.Model):
    _name = "contract.price.purchase"

    name = fields.Char(string='Reference')
    product_id = fields.Many2one('product.product', string='Item name', related='contract_id.product_id', store=True)
    date_price = fields.Date(string='Date', related='contract_id.date_order', store=True)
    exchange = fields.Many2one('exchange.india', related='product_id.exchange_id', string='Exchange', store=True)
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
    outturn = fields.Float(string='Outturn %', compute='compute_outturn', store=True, readonly=False)
    open_qty = fields.Float(string='Open Qty', related='contract_id.open_qty', store=True)
    outturn_qty = fields.Float(string='OT Qty', compute='compute_outturn_qty', store=True)
    total_allocated_qty = fields.Float(string='Total Allocated', related='contract_id.total_allocated_qty', store=True)
    open_p_contract = fields.Float(string='Open P Contract', compute='compute_outturn_qty', store=True)

    gross_qty = fields.Float(string='Gross Qty(SN)', related='contract_id.gross_qty', store=True)

    hide_allocation = fields.Boolean(string='Hide Allocation', related='contract_id.open_qty_check', store=True)

    a_ab_price = fields.Float(string='A /AB Price', compute='_compute_a_ab_price', store=True)
    validate = fields.Float(string='Validate', compute='_compute_a_ab_price', store=True)

    @api.depends('market_price', 'a_differential', 'ab_differential', 'fob')
    def _compute_a_ab_price(self):
        for rec in self:
            rec.a_ab_price = rec.market_price + rec.a_differential + rec.ab_differential
            rec.validate = rec.fob - rec.a_ab_price

    @api.depends('outturn', 'quantity', 'total_allocated_qty', 'gross_qty')
    def compute_outturn_qty(self):
        for rec in self:
            rec.outturn_qty = (rec.outturn * rec.gross_qty)/100
            rec.open_p_contract = rec.outturn_qty - rec.total_allocated_qty

    @api.depends('product_id', 'product_id.outturn')
    def compute_outturn(self):
        for rec in self:
            rec.outturn = rec.product_id.outturn

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

    @api.constrains('contract_id')
    def check_contract_id(self):
        for rec in self:
            check_contract = self.env['contract.price.purchase'].search([
                ('contract_id', '=', rec.contract_id.id),
                ('id', '!=', rec.id)
            ], limit=1)
            if check_contract:
                raise UserError(_("You cannot create multiple contract!!"))