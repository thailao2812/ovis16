# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from datetime import datetime, date, timedelta


class AccountMove(models.Model):
    _inherit = 'account.move'

    request_payment_invoice_ids = fields.One2many('request.payment.invoice', 'invoice_id', string='Request Payment Invoice')

    @api.depends('purchase_contract_invoice_ids.quantity', 'purchase_contract_invoice_ids.amount_allocated_untaxed',
                 'purchase_contract_id', 'state',
                 'purchase_contract_id.state', 'purchase_contract_id.type', 'amount_untaxed', 'amount_tax',
                 'amount_total', 'request_payment_invoice_ids', 'request_payment_invoice_ids.allocate_amount','request_payment_invoice_ids.tax_amount',
                 'purchase_contract_invoice_ids.amount_allocated_tax',
                 'purchase_contract_invoice_ids.amount_allocated_total')
    def _compute_allocated_amount(self):
        for rec in self:
            rec.remain_taxed_amount = rec.amount_tax - sum(rec.request_payment_invoice_ids.filtered(lambda x: x.state == 'paid').mapped('tax_amount'))
