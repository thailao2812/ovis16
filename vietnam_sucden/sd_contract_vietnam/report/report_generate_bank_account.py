# -*- encoding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.addons.report_aeroo.report_parser import Parser
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
from num2words import num2words

from pytz import timezone
from datetime import datetime, timedelta


class Parser(models.AbstractModel):
    _name = 'report.report_generate_bank_account'
    _inherit = ['report.report_aeroo.abstract']
    _description = 'report.report_generate_bank_account'

    def _set_localcontext(self):
        localcontext = super(Parser, self)._set_localcontext()
        localcontext.update({
            'get_same_bank': self.get_same_bank,
            'get_different_bank': self.get_different_bank
        })
        return localcontext

    def get_same_bank(self, wizard):
        # Set bank default
        journal = self.env['account.journal'].browse(wizard.journal_id.id)
        # Get name bank default
        name = journal.name.split('-')[0]
        value = []
        for request in wizard.request_payment_ids:
            for payment in request.request_payment_ids.filtered(lambda x: x.state == 'draft'):
                if name.lower() in payment.partner_bank_id.bank_id.bic.lower() or request.partner_bank_id.bank_id.bic.lower() in name.lower():
                    value.append({
                        'total': "{:,}".format(int(payment.amount)),
                        'supplier': payment.partner_id.name,
                        'account': request.account_no,
                        'memo': payment.ref
                    })
        return value

    def get_different_bank(self, wizard):
        journal = self.env['account.journal'].browse(wizard.journal_id.id)
        name = journal.name.split('-')[0]
        value = []
        for request in wizard.request_payment_ids:
            for payment in request.request_payment_ids.filtered(lambda x: x.state == 'draft'):
                if name.lower() not in payment.partner_bank_id.bank_id.bic.lower() or payment.partner_bank_id.bank_id.bic.lower() not in name.lower():
                    value.append({
                        'total': "{:,}".format(int(payment.amount)),
                        'supplier': request.partner_id.name,
                        'account': request.account_no,
                        'memo': payment.ref,
                        'bank': payment.partner_bank_id.bank_id.bic + ' ' + payment.partner_bank_id.bank_id.name,
                        'address': payment.partner_bank_id.bank_id.street,
                        'branch': payment.partner_bank_id.bank_id.city,
                    })
        return value