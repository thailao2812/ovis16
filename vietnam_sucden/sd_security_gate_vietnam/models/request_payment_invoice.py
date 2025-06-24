# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
import math


class RequestPaymentInvoice(models.Model):
    _name = 'request.payment.invoice'

    request_payment_id = fields.Many2one('request.payment', ondelete='cascade')
    state = fields.Selection(related='request_payment_id.state', string='State', store=True)
    invoice_id = fields.Many2one('account.move', string='Invoice')
    allocate_amount = fields.Float(string='Allocate Amount')
    remaining_amount = fields.Float(string='Remaining Amount', compute='_compute_remaining_amount', store=True)
    paid_amount = fields.Float(string='Paid Amount')

    account_payment_ids = fields.One2many('account.payment', 'request_payment_invoice_id', string='Account Payment')

    @api.depends('invoice_id', 'allocate_amount', 'state')
    def _compute_remaining_amount(self):
        for rec in self:
            rec.remaining_amount = rec.invoice_id.amount_residual