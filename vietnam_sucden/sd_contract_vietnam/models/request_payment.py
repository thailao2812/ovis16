# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from num2words import num2words

class RequestPayment(models.Model):
    _inherit = 'request.payment'

    @api.model
    def _default_currency_id(self):
        currency_ids = self.env.user.company_id.second_currency_id.id
        return currency_ids

    product_id = fields.Many2one('product.product', related='purchase_contract_id.product_id', store=True)
    grn_done_ids = fields.Many2many('stock.picking', 'grn_done_id_ref', string='GRN 100%')
    grn_ready_ids = fields.Many2many('stock.picking', 'grn_ready_id_ref', string='GRN 90%')
    grn_fot_done_ids = fields.Many2many('stock.picking', 'grn_fot_done_id_ref', string='GRN FOT 100%')

    delivery_registration_ktn_ids = fields.One2many('delivery.katoen', 'request_payment_id')
    certificate_id = fields.Many2one('ned.certificate', related='purchase_contract_id.certificate_id', store=True)
    quantity_contract = fields.Float(string='Quantity', related='purchase_contract_id.total_qty', store=True)
    paid_quantity = fields.Float(string='Paid Quantity', compute='compute_paid_quantity', store=True, digits=(12, 0))
    balance_quantity = fields.Float(string='Balance Quantity', compute='compute_paid_quantity', store=True, digits=(12, 0))
    date_contract = fields.Date(string='Fixation Date', related='purchase_contract_id.date_order', store=True)
    price_npe = fields.Float(string='Market Price')
    fix_price = fields.Float(string='Fixation Price', compute='compute_fix_price', store=True, digits=(12, 0))
    currency_id = fields.Many2one("res.currency", string="Currency", readonly=True, required=True,
                                  states={'draft': [('readonly', False)]}, default=_default_currency_id)
    amount_untaxed = fields.Monetary(string='Contract Value (not include Tax)', related='purchase_contract_id.amount_untaxed', store=True)
    total_value = fields.Float(string='Total', compute='compute_total_value', store=True, digits=(12, 0))
    deposit_amount = fields.Float(string='Deposit Amount', related='purchase_contract_id.deposit_amount', store=True, digits=(12, 0))
    liquidation_amount = fields.Float(string='Liquidation Amount', compute='compute_liquidation_amount', store=True, readonly=False, digits=(12, 0))
    total_payment = fields.Float(string='Total Payment', compute='compute_total_value', store=True)
    amount_in_text = fields.Char(string='Amount in text', compute='compute_amount_in_text', store=False)
    partner_id = fields.Many2one('res.partner', string='Partner', related='purchase_contract_id.partner_id', store=True)
    # request_amount = fields.Float(string='Request Amount', digits=(12, 0), compute='_compute_request_amount',
    #                               store=True, readonly=False)

    @api.depends('purchase_contract_id', 'purchase_contract_id.type', 'purchase_contract_id.relation_price_unit',
                 'price_npe')
    def compute_fix_price(self):
        for rec in self:
            rec.fix_price = 0
            if rec.purchase_contract_id and rec.purchase_contract_id.type == 'purchase':
                rec.fix_price = rec.purchase_contract_id.relation_price_unit
            if rec.purchase_contract_id and rec.purchase_contract_id.type == 'consign':
                rec.fix_price = rec.price_npe * 70/100

    # @api.depends('payment_quantity', 'fix_price', 'liquidation_amount', 'deposit_amount')
    # def _compute_request_amount(self):
    #     for rec in self:
    #         if rec.type == 'purchase':
    #             rec.request_amount = (rec.payment_quantity * rec.fix_price) - rec.deposit_amount - rec.liquidation_amount
    #         if rec.type == 'consign':
    #             rec.request_amount = (rec.payment_quantity * rec.fix_price) - rec.deposit_amount - rec.liquidation_amount

    @api.depends('request_amount')
    def compute_amount_in_text(self):
        for rec in self:
            rec.amount_in_text = ''
            if rec.request_amount > 0:
                amount_in_words = num2words(rec.request_amount, lang='vi_VN')
                amount_in_words = amount_in_words[0].upper() + amount_in_words[1:]
                amount_in_words = amount_in_words + ' ' + 'đồng'
                rec.amount_in_text = amount_in_words

    @api.depends('name')
    def compute_liquidation_amount(self):
        for rec in self:
            if int(rec.name) == 1:
                rec.liquidation_amount = 10000000
            else:
                rec.liquidation_amount = 0

    @api.depends('payment_quantity', 'fix_price', 'liquidation_amount', 'deposit_amount')
    def compute_total_value(self):
        for rec in self:
            rec.total_value = rec.payment_quantity * rec.fix_price
            rec.total_payment = (rec.payment_quantity * rec.fix_price) - rec.deposit_amount - rec.liquidation_amount

    @api.depends('purchase_contract_id', 'purchase_contract_id.request_payment_ids',
                 'purchase_contract_id.request_payment_ids.name',
                 'purchase_contract_id.request_payment_ids.payment_quantity', 'name')
    def compute_paid_quantity(self):
        for rec in self:
            if int(rec.name) > 1:
                paid_quantity = sum(rec.purchase_contract_id.request_payment_ids._origin.filtered(lambda x: int(x.name) < int(rec.name)).mapped('payment_quantity'))
                rec.paid_quantity = paid_quantity
                rec.balance_quantity = rec.quantity_contract - rec.paid_quantity
            else:
                rec.paid_quantity = 0
                rec.balance_quantity = rec.quantity_contract - rec.paid_quantity

    # @api.depends('quantity_contract', 'paid_quantity')
    # def compute_balance_quantity(self):
    #     for rec in self:
    #         rec.balance_quantity = rec.quantity_contract - rec.paid_quantity


class DeliveryKatoen(models.Model):
    _name = 'delivery.katoen'

    request_payment_id = fields.Many2one('request.payment')
    name = fields.Char(string='Truck No.')
    quantity = fields.Float(string='Quantity')
