# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    is_final_payment = fields.Boolean(string='Is Final Payment')

    def action_post(self):
        res = super(AccountPayment, self).action_post()
        if self.env.context.get('final_payment') or self.is_final_payment:
            if self.purchase_contract_id:
                if self.purchase_contract_id.state_final_payment == 'director':
                    self.purchase_contract_id.state_final_payment = 'paid'
        return res