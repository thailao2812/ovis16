# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import datetime, time, timedelta


class WizardCreateMultiplePayment(models.TransientModel):
    _name = 'wizard.create.multiple.payment'
    _description = "Wizard Create Multiple Payment"

    line_ids = fields.One2many('wizard.create.multiple.payment.line', 'wizard_id', string="Lines")

    def action_confirm(self):
        active_id = self.env.context.get('active_id')
        request_payment_id = self.env['request.payment'].browse(active_id)
        for line in self.line_ids:
            if not line.journal_id and line.allocate_amount != line.paid_amount:
                raise UserError(_("Journal is required"))
            if line.request_amount <= 0 and line.allocate_amount != line.paid_amount:
                raise UserError(_("Request amount must be greater than 0"))
            if line.paid_amount + line.request_amount > line.allocate_amount:
                print(line.paid_amount, line.request_amount)
                raise UserError(_("Paid amount must be less than or equal to allocate amount"))
            if line.request_amount > 0:
                self.env['account.payment'].create({
                    'journal_id': line.journal_id.id,
                    'date': datetime.today(),
                    'payment_type': 'outbound',
                    'amount': line.request_amount,
                    'extend_payment': 'payment',
                    'partner_type': 'supplier',
                    'ref': 'Thanh toán tiền theo %s' % request_payment_id.purchase_contract_id.name,
                    'partner_bank_id': request_payment_id.partner_bank_id.id,
                    'request_payment_id': request_payment_id.id,
                    'responsible': self.env.user.name,
                    'partner_id': request_payment_id.partner_id.id,
                    'request_payment_invoice_id': request_payment_id.invoice_ids.filtered(lambda r: r.invoice_id.id == line.invoice_id.id).id,
                })

    @api.model
    def default_get(self, fields):
        res = super(WizardCreateMultiplePayment, self).default_get(fields)
        active_id = self.env.context.get('active_id')
        request_payment_id = self.env['request.payment'].browse(active_id)
        invoice_ids = request_payment_id.invoice_ids
        line_ids = []
        for line in invoice_ids:
            line_ids.append((0, 0, {
                'invoice_id': line.invoice_id.id,
                'paid_amount': line.paid_amount,
                'allocate_amount': line.allocate_amount
            }))
        res['line_ids'] = line_ids
        return res




class WizardCreateMultiplePaymentLine(models.TransientModel):
    _name = 'wizard.create.multiple.payment.line'
    _description = "Wizard Create Multiple Payment Line"

    wizard_id = fields.Many2one('wizard.create.multiple.payment')
    invoice_id = fields.Many2one('account.move')
    journal_id = fields.Many2one('account.journal', string='Journal')
    request_amount = fields.Float(string="Request Amount")
    allocate_amount = fields.Float(string='Allocate Amount')
    paid_amount = fields.Float(string="Paid Amount")