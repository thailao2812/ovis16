# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError, AccessError, RedirectWarning
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
import math


class AccountMove(models.Model):
    _inherit = "account.move"

    amount_total_india = fields.Monetary(string='Total Amount (rounding)', store=True, readonly=True,
                                         compute='_compute_amount', )

    @api.depends('invoice_date', 'company_id')
    def _compute_date(self):
        for move in self:
            if not move.invoice_date:
                if not move.date:
                    move.date = fields.Date.context_today(self)
                continue
            accounting_date = move.invoice_date
            if not move.is_sale_document(include_receipts=True):
                accounting_date = move._get_accounting_date(move.invoice_date, move._affect_tax_report())
            if accounting_date and accounting_date != move.date:
                move.date = accounting_date
                # might be protected because `_get_accounting_date` requires the `name`
                # self.env.add_to_compute(self._fields['name'], move)

    def custom_round(self, number: float) -> int:
        if number - round(number) == 0.5:
            return math.ceil(number)
        else:
            return round(number)

    @api.depends(
        'line_ids.matched_debit_ids.debit_move_id.move_id.payment_id.is_matched',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.matched_credit_ids.credit_move_id.move_id.payment_id.is_matched',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.balance',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state',
        'line_ids.full_reconcile_id')
    def _compute_amount(self):
        for move in self:
            total_untaxed, total_untaxed_currency = 0.0, 0.0
            total_tax, total_tax_currency = 0.0, 0.0
            total_residual, total_residual_currency = 0.0, 0.0
            total, total_currency = 0.0, 0.0

            for line in move.line_ids:
                if move.is_invoice(True):
                    # === Invoices ===
                    if line.display_type == 'tax' or (line.display_type == 'rounding' and line.tax_repartition_line_id):
                        # Tax amount.
                        total_tax += line.balance
                        total_tax_currency += line.amount_currency
                        total += line.balance
                        total_currency += line.amount_currency
                    elif line.display_type in ('product', 'rounding'):
                        # Untaxed amount.
                        total_untaxed += line.balance
                        total_untaxed_currency += line.amount_currency
                        total += line.balance
                        total_currency += line.amount_currency
                    elif line.display_type == 'payment_term':
                        # Residual amount.
                        total_residual += line.amount_residual
                        total_residual_currency += line.amount_residual_currency
                else:
                    # === Miscellaneous journal entry ===
                    if line.debit:
                        total += line.balance
                        total_currency += line.amount_currency

            sign = move.direction_sign
            move.amount_untaxed = sign * total_untaxed_currency
            move.amount_tax = sign * total_tax_currency
            move.amount_total = sign * total_currency
            move.amount_total_india = self.custom_round(sign * total_currency)
            move.amount_residual = -sign * total_residual_currency
            move.amount_untaxed_signed = -total_untaxed
            move.amount_tax_signed = -total_tax
            move.amount_total_signed = abs(total) if move.move_type == 'entry' else -total
            move.amount_residual_signed = total_residual
            move.amount_total_in_currency_signed = abs(move.amount_total) if move.move_type == 'entry' else -(
                        sign * move.amount_total)


    @api.onchange('name', 'highest_name')
    def _onchange_name_warning(self):
        print(123)

    def re_calculate_debit_credit(self):
        date = self.invoice_date
        if self.currency_id != self.company_id.currency_id:
            rate_checking = self.env['res.currency.rate'].search([
                ('name', '=', date)
            ])
            if rate_checking:
                debit_line = self.invoice_line_ids.filtered(lambda x: x.debit > 0)
                debit_line.with_context(check_move_validity=False,action_from_account_payment=True,skip_onchange=True).debit = abs(debit_line.amount_currency) * rate_checking.rate or 0
                credit_line = self.invoice_line_ids.filtered(lambda x: x.credit > 0)
                credit_line.with_context(check_move_validity=False, action_from_account_payment=True, skip_onchange=True).credit = abs(credit_line.amount_currency) * rate_checking.rate or 0