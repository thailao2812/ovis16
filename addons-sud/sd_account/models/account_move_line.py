
# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

class ACcountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.model
    def compute_amount_fields(self, amount, src_currency, company_currency, invoice_currency=False):
        """ Helper function to compute value for fields debit/credit/amount_currency based on an amount and the currencies given in parameter"""
        amount_currency = False
        currency_id = False
        if src_currency and src_currency != company_currency:
            amount_currency = amount
            amount = src_currency.with_context(self._context).compute(amount, company_currency)
            currency_id = src_currency.id
        debit = amount > 0 and amount or 0.0
        credit = amount < 0 and -amount or 0.0
        if invoice_currency and invoice_currency != company_currency and not amount_currency:
            amount_currency = src_currency.with_context(self._context).compute(amount, invoice_currency)
            currency_id = invoice_currency.id
        return debit, credit, amount_currency, currency_id
    
    
    rate_type = fields.Selection([('transaction_rate', 'Transaction Rate'),
                                  ('average_rate', 'Average Rate')],
                                 string='Rate Type', default='average_rate', copy=True)
    
    currency_ex_rate = fields.Float(string='Currency Rate', copy=False, readonly=False)
    second_ex_rate = fields.Float(string='2nd Rate', copy=False, readonly=True)
    second_amount = fields.Float(string='2nd Amount',  copy=False, readonly=True)
    second_currency_id = fields.Many2one(related='company_id.second_currency_id', store=True, string='2nd Currency', readonly=True, copy=False)
    
    group_cp = fields.Integer(string="Group CP", default=0)
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account', readonly=True, index=True, store=True, related='move_id.account_analytic_id')
    
    