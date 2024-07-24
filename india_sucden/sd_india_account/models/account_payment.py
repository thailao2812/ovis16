# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class AccountPayment(models.Model):
    _inherit = "account.payment"

    @api.model
    def default_get(self, fields):
        rec = super(AccountPayment, self).default_get(fields)
        active_id = self._context.get('active_id')
        if self._context.get('active_model') and self._context.get('active_model') == 'request.payment':
            request = self.env['request.payment'].browse(active_id)
            if request.purchase_contract_id:
                rec['currency_id'] = request.purchase_contract_id.currency_id.id
                rec['payment_type'] = 'outbound'
                rec['partner_id'] = request.purchase_contract_id.partner_id.id
                rec['purchase_contract_id'] = request.purchase_contract_id.id
                rec['request_payment_id'] = active_id
                rec['responsible'] = self.env.user.name

                request_amount = 0
                for payment in request.request_payment_ids.filtered(lambda x: x.state == 'posted'):
                    request_amount += payment.amount

                rec['amount'] = request.request_amount - (request_amount or 0.0)

                if request.purchase_contract_id.type not in ('purchase', 'ptbf'):
                    rec['extend_payment'] = 'payment'
                    rec['ref'] = u'Advance for ' + request.purchase_contract_id.name
                else:
                    rec['extend_payment'] = 'payment'
                    rec['ref'] = u'Payment for ' + request.purchase_contract_id.name

                # if request.purchase_contract_id.type !='purchase':
                #     # rec['extend_payment'] = 'advance'
                #     rec['extend_payment'] = 'payment'
                #     rec['ref'] = 'Advance - ' + request.purchase_contract_id.name
                # else:
                #     rec['extend_payment'] = 'payment'
                #     rec['ref'] = 'Payment - ' + request.purchase_contract_id.name

        if self._context.get('active_model') and self._context.get('active_model') == 'purchase.contract':
            contract_id = self.env[self._context.get('active_model')].browse(active_id)
            if contract_id.type == 'purchase':
                rec['currency_id'] = contract_id.currency_id.id
                rec['payment_type'] = 'outbound'
                rec['partner_id'] = contract_id.partner_id.id
                rec['purchase_contract_id'] = contract_id.id
                rec['ref'] = u'Payment for ' + contract_id.name
                rec['extend_payment'] = 'payment'
                rec['amount'] = contract_id.amount_total

            if contract_id.type == 'ptbf':
                rec['ref'] = contract_id.name
                rec['currency_id'] = contract_id.currency_id.id
                rec['payment_type'] = 'inbound'
                rec['partner_id'] = contract_id.partner_id.id
                rec['purchase_contract_id'] = contract_id.id
                rec['communication'] = u'Get a deposit for ' + contract_id.name
                rec['extend_payment'] = 'payment'
                rec['amount'] = contract_id.amount_total

        return rec
