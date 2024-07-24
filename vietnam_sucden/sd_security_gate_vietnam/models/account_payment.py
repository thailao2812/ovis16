# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from datetime import datetime, date, timedelta


class AccountPayment(models.Model):
    _inherit = 'account.payment'

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
        return res