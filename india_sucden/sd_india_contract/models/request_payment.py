# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import AccessError, UserError, ValidationError
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
import math
from datetime import datetime, date, timedelta


class RequestPayment(models.Model):
    _inherit = "request.payment"

    provisional_amount = fields.Float(string='Interest Temporary', compute='_compute_provisional_amount', digits=(12, 0))

    chinhanh = fields.Char(string='Branch', required=True)

    songay = fields.Integer(string='Days')

    related_holder = fields.Char(string='Bank Holder Name')

    ifsc_code = fields.Char(string='IFSC Code', related='partner_bank_id.ifsc_code', store=True)

    deduction_value = fields.Float(string='Deduction Request Amount')
    deduction_quantity = fields.Float(string='Quantity Adjustment')
    branch = fields.Char(string='Branch')
    estate_name = fields.Char(string='Estate Name', related='partner_id.estate_name', store=True)
    pan_number = fields.Char(string='Pan Number', related='partner_id.pan_number', store=True)
    vendor_invoice_number = fields.Char(string='Vendor Invoice Number')
    vendor_invoice_date = fields.Date(string='Vendor Invoice Date')
    product_id = fields.Many2one('product.product', string='Product', related='purchase_contract_id.product_id', store=True)
    price = fields.Float(string='Price/Qty', compute='compute_price_request_payment', store=True)
    use_payment_for = fields.Selection([
        ('advance', 'Advance Payment'),
        ('payment', 'Against Delivery')
    ], string='Type Payment', default=None)
    payment_refunded = fields.Float(string='Refunded', compute='_compute_refunded', digits=(12, 0), store=True)
    open_advance = fields.Float(string='Open Advance', compute='_compute_refunded', digits=(12, 0), store=True)
    source_document_contract = fields.Char(string='Source Document', related='purchase_contract_id.origin', store=True)
    invoice_amount = fields.Float(string='Invoice Amount', compute='compute_invoice_amount', store=True)
    state = fields.Selection(selection='_get_new_state', string='State', readonly=False, copy=False, index=True, default='request')
    tds_assessable_value = fields.Float(string='TDS Assessable Value')
    tds_amount = fields.Float(string='TDS Amount', compute='compute_tds_amount', store=True)
    final_request_payment = fields.Float(string='Net Payment', compute='compute_net_payment', store=True)
    financial_year_id = fields.Many2one('financial.year', string='Financial year')
    date_approve = fields.Date(string='Date Approve')

    @api.depends('request_amount', 'tds_amount', 'tds_assessable_value', 'financial_year_id')
    def compute_net_payment(self):
        for rec in self:
            rec.final_request_payment = rec.request_amount - rec.tds_amount

    def custom_round(self, number: float) -> int:
        if number - round(number) == 0.5:
            return math.ceil(number)
        else:
            return round(number)

    @api.depends('partner_id', 'request_amount', 'financial_year_id', 'type', 'tds_assessable_value')
    def compute_tds_amount(self):
        for rec in self:
            rec.tds_amount = 0
            financial_year = rec.financial_year_id
            if financial_year:
                if rec.partner_id.pan_number:
                    rec.tds_amount = self.custom_round(rec.tds_assessable_value * (financial_year.percent_for_pan / 100))
                else:
                    rec.tds_amount = self.custom_round(rec.tds_assessable_value * (financial_year.percent_unpan / 100))

    @api.model
    def _get_new_state(self):
        return [
        ('request', 'Request'),
        ('purchasing', 'Purchasing'),
        ('approved', 'Accounting 1st'),
        ('accounting_2', 'Accounting 2nd'),
        ('approved_director', 'Approve by Director'),
        ('paid', 'Paid')
    ]

    @api.depends('payment_quantity', 'price')
    def compute_invoice_amount(self):
        for rec in self:
            if rec.price > 0:
                rec.invoice_amount = rec.payment_quantity * rec.price
            else:
                rec.invoice_amount = 0

    @api.depends('request_amount', 'payment_quantity', 'use_payment_for', 'provisional_price', 'purchase_contract_id.total_qty', 'purchase_contract_id.amount_untaxed')
    def compute_price_request_payment(self):
        for rec in self:
            if rec.use_payment_for == 'payment':
                if rec.purchase_contract_id.total_qty > 0:
                    rec.price = rec.purchase_contract_id.amount_untaxed / rec.purchase_contract_id.total_qty
                else:
                    rec.price = 0
            else:
                rec.price = rec.provisional_price


    @api.onchange('partner_bank_id')
    def _onchange_partner_bank(self):
        res = super(RequestPayment, self)._onchange_partner_bank()
        if self.partner_bank_id:
            self.related_holder = self.partner_bank_id.related_holder
            self.branch = self.partner_bank_id.branch
        return res

    def action_request_register_payment(self):
        if self.total_remain == 0:
            raise UserError(_("You don't need to payment more for this Contract!!"))
        if any(self.request_payment_ids.filtered(lambda x: x.state not in ['posted', 'cancel'])):
            raise UserError(_("You cannot create more payment, please posted or cancel the exist payment"))
        return {
            'name': _('Register Payment'),
            'res_model': 'account.payment',
            'view_mode': 'form',
            # 'domain':self.request_payment_ids.ids,
            'context': {
                'active_model': 'request.payment',
                'active_ids': self.ids,
                'default_partner_type': 'supplier',
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def btt_approved(self):
        if self.purchase_contract_id.state != 'approved':
            raise UserError(_("You cannot approve this request payment when Contract not in Approve State, please check again!!!"))
        self.date_approve = datetime.now()
        self.state = 'approved'

    @api.depends('request_payment_ids', 'request_amount', 'advance_payment_quantity', 'tds_amount', 'date_approve')
    def _compute_request_payment(self):
        for request in self:
            total_payment = 0.0
            for line in request.request_payment_ids.filtered(lambda x: x.state == 'posted'):
                total_payment += line.amount
            request.total_payment = total_payment
            #             if not request.advance_price:
            #                 request.advance_payment_quantity = 0.0
            #             else:
            #                 request.advance_payment_quantity = request.request_amount / request.advance_price

            if not request.advance_payment_quantity:
                request.advance_price = 0.0
            else:
                request.advance_price = request.request_amount / request.advance_payment_quantity

            request.total_remain = request.request_amount - total_payment
            if not request.date_approve:
                request.state = 'request'
            if request.date_approve and total_payment == 0:
                request.state = 'approved'
            if request.date_approve and (request.total_remain == 0.0 and total_payment != 0):
                request.state = 'paid'
            if request.total_remain == 0.0:
                if total_payment != 0:
                    request.state = 'paid'
            if request.tds_amount > 0:
                if request.total_remain == request.tds_amount:
                    request.state = 'paid'





