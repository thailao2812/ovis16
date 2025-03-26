# -*- encoding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError


class WizardGenerateBankAccount(models.TransientModel):
    _name = 'wizard.generate.bank.account'
    _description = 'Generate Bank Account'

    journal_ids = fields.Many2many('account.journal', string='Journals')
    request_payment_ids = fields.Many2many('request.payment', string='Requests')
    journal_id = fields.Many2one('account.journal', string='Journal', required=True)
    name = fields.Text(string='Name')

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if self.env.context.get('active_model') == 'request.payment':
            request_payment = self.env['request.payment'].browse(self.env.context.get('active_ids'))
            res['request_payment_ids'] = [(6, 0, request_payment.ids)]
            error_messages = []

            for req in request_payment:
                has_draft = req.request_payment_ids.filtered(lambda r: r.state == 'draft')
                if not has_draft:
                    contract_name = req.purchase_contract_id.name or 'No Contract'
                    error_messages.append(
                        _("Request %(req_name)s của hợp đồng %(contract)s đang không đủ dữ liệu") % {
                            'req_name': req.name,
                            'contract': contract_name,
                        }
                    )
            if error_messages:
                res['name'] = '\n'.join(error_messages)
            else:
                all_journals = self.env['account.journal']
                for req in request_payment:
                    draft_lines = req.request_payment_ids.filtered(lambda line: line.state == 'draft')
                    all_journals |= draft_lines.mapped('journal_id')

                res['journal_ids'] = [(6, 0, all_journals.ids)]

        return res
        
    def action_generate_bank_account(self):
        return self.env.ref('sd_contract_vietnam.report_generate_bank_account').report_action(self)