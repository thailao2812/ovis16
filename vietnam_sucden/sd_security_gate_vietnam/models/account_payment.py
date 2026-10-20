# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from datetime import datetime, date, timedelta


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    request_payment_invoice_id = fields.Many2one('request.payment.invoice', string='Request Payment Invoice')

    def action_post(self):
        res = super(AccountPayment, self).action_post()
        active_id = self._context.get('active_id')
        # if self._context.get('active_model') and self._context.get('active_model') ==  'purchase.contract':
        #     contract_id = self.env[self._context.get('active_model')].browse(active_id)

        if self.purchase_contract_id:
            if self.request_payment_id:
                self.env['user.process.state'].create({
                    'request_payment_id': self.request_payment_id.id,
                    'user_id': self.env.user.id,
                    'date': datetime.today(),
                    'state': 'Paid by %s' % self.env.user.name
                })
        if self.request_payment_invoice_id:
            self.request_payment_invoice_id.paid_amount += self.amount
            payment_line = self.line_ids.filtered(
                lambda line: line.account_id.account_type == 'liability_payable'
            )
            bill_line = self.request_payment_invoice_id.invoice_id.line_ids.filtered(
                lambda line: line.account_id.account_type == 'liability_payable'
            )
            reconcile_wanted = self.env['account.reconcile.wizard'].with_context(
                active_model='account.move.line',
                active_ids=[bill_line.id, payment_line.id],
            ).new({'allow_partials': True})
            reconcile_wanted.reconcile()
        return res

    def action_draft(self):
        res = super(AccountPayment, self).action_draft()
        if self.request_payment_invoice_id:
            self.request_payment_invoice_id.paid_amount = 0
        return res

    @api.model
    def default_get(self, fields):
        rec = super(AccountPayment, self).default_get(fields)

        return rec