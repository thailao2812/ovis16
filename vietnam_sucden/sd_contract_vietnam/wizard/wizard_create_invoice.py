# -*- encoding: utf-8 -*-
from pyparsing import line_end

from odoo import fields, models, api, _
import base64
import xlrd
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class WizardCreateInvoice(models.TransientModel):
    _name = 'wizard.create.invoice'

    def _default_journal(self):
        company_id = self.env.user.company_id.id
        return self.env['account.journal'].search([('company_id', '=', company_id), ('type', '=', 'purchase')], limit=1).id or False

    contract_id = fields.Many2one('purchase.contract', string='Purchase Contract')
    type = fields.Selection(related='contract_id.type', string='Type', readonly=True)
    quantity = fields.Float(string='Quantity', digits=(16,0))
    journal_id = fields.Many2one('account.journal', string='Journal', default=_default_journal)
    invoice_number = fields.Char(string='Invoice Number')
    invoice_denominator = fields.Char(string='Invoice Denominator')
    date = fields.Date(string='Invoice Date')
    price_unit = fields.Float(string='Price Unit')
    paid_amount = fields.Float(string='Paid Amount')

    # Convert contract
    is_converted = fields.Boolean(string='Is Converted')
    invoice_converted_ids = fields.Many2many('account.move', string='Invoice Converted')
    invoice_origin_id = fields.Many2one('account.move', string='Invoice Origin')
    amount_different = fields.Float(string='Amount Different')

    @api.model
    def default_get(self, fields):
        res = super(WizardCreateInvoice, self).default_get(fields)
        active_id = self.env.context.get('active_id')
        purchase_contract = self.env['purchase.contract'].browse(active_id)
        if purchase_contract:
            res['contract_id'] = purchase_contract.id
            res['quantity'] = purchase_contract.invoice_qty_remain
            if purchase_contract.type == 'purchase' and purchase_contract.purchase_contract_invoice_ids and purchase_contract.origin and purchase_contract.nvp_ids:
                res['is_converted'] = True
                res['invoice_converted_ids'] = purchase_contract.purchase_contract_invoice_ids.mapped('move_id')
        return res

    def _prepare_invoice_line(self, move_line, invoice_id, invoice_vals, price_unit):
        name = move_line.product_id.name or ''
        origin = move_line.product_id.name or ''
        account_id = move_line.product_id.categ_id.property_account_expense_categ_id.id or False

        return {'name': name,
                'display_type': 'product',
                'move_id': invoice_id.id, 'product_id': move_line.product_id.id,
                'account_id': account_id, 'price_unit': price_unit or 0.0,
                'quantity': self.quantity,
                'product_uom_id': move_line.product_uom and move_line.product_uom.id or False,
                'tax_ids': self.contract_id.vat_id.ids
                }

    def _prepare_default_values(self, move):
        if move.move_type in ('in_refund', 'out_refund'):
            type = 'in_invoice' if move.move_type == 'in_refund' else 'out_invoice'
        else:
            type = move.move_type
        default_values = {'ref': self.invoice_number, 'date': self.date or move.date,
                          'invoice_date': self.date or move.date,
                          'journal_id': self.journal_id and self.journal_id.id or move.journal_id.id,
                          'invoice_payment_term_id': None, 'invoice_denominator': self.invoice_denominator,
                          'debit_origin_id': move.id, 'move_type': type, 'line_ids': [(5, 0, 0)]}
        return default_values

    def create_debit(self):
        self.ensure_one()
        new_moves = self.env['account.move']
        for move in self.invoice_origin_id.with_context(include_business_fields=True): #copy sale/purchase links
            print(move)
            default_values = self._prepare_default_values(move)
            new_move = move.copy(default=default_values)
            company_id = self.env.user.company_id
            if not company_id.stock_account_coffee_id:
                raise UserError(_("Please set stock account coffee in company"))
            move_line = self.env['account.move.line'].create({
                'product_id': self.contract_id.product_id.id,
                'display_type': 'product',
                'move_id': new_move.id,
                'account_id': company_id.stock_account_coffee_id.id if company_id.stock_account_coffee_id else False,
                'quantity': 1,
                'price_unit': self.amount_different,
                'tax_ids': self.contract_id.vat_id.ids,
            })
            move_msg = _(
                "This debit note was created from: %s",
                move._get_html_link(),
            )
            new_move.message_post(body=move_msg)
            new_moves |= new_move
            new_move.purchase_contract_id = self.contract_id.id
        return True

    def create_credit(self):
        moves = self.invoice_origin_id

        # Create default values.
        partners = moves.company_id.partner_id + moves.commercial_partner_id

        bank_ids = self.env['res.partner.bank'].search([
            ('partner_id', 'in', partners.ids),
            ('company_id', 'in', moves.company_id.ids + [False]),
        ], order='sequence DESC')
        partner_to_bank = {bank.partner_id: bank for bank in bank_ids}
        default_values_list = []
        company_id = self.env.user.company_id
        if not company_id.stock_account_coffee_id:
            raise UserError(_("Please set stock account coffee in company"))
        for move in moves:
            if move.is_outbound():
                partner = move.company_id.partner_id
            else:
                partner = move.commercial_partner_id
            default_values_list.append({
                'partner_bank_id': partner_to_bank.get(partner, self.env['res.partner.bank']).id,
                **self._prepare_default_reversal(move),
            })
        batches = [
            [self.env['account.move'], [], True],  # Moves to be cancelled by the reverses.
            [self.env['account.move'], [], False],  # Others.
        ]
        refund_method = 'modify'
        for move, default_vals in zip(moves, default_values_list):
            is_cancel_needed = False
            batch_index = 0 if is_cancel_needed else 1
            batches[batch_index][0] |= move
            batches[batch_index][1].append(default_vals)

        # Handle reverse method.
        moves_to_redirect = self.env['account.move']
        for moves, default_values_list, is_cancel_needed in batches:
            new_moves = moves._reverse_moves(default_values_list, cancel=is_cancel_needed)

            # if refund_method == 'modify':
            #     moves_vals_list = []
            #     for move in moves.with_context(include_business_fields=True):
            #         moves_vals_list.append(move.copy_data({'date': self.date})[0])
            #     new_moves = self.env['account.move'].create(moves_vals_list)

            moves_to_redirect |= new_moves
        moves_to_redirect.invoice_line_ids.unlink()
        moves_to_redirect.line_ids.unlink()
        moves_to_redirect.purchase_contract_id = self.contract_id.id
        move_line = self.env['account.move.line'].create({
            'product_id': self.contract_id.product_id.id,
            'display_type': 'product',
            'move_id': moves_to_redirect.id,
            'account_id': company_id.stock_account_coffee_id.id if company_id.stock_account_coffee_id else False,
            'quantity': 1,
            'price_unit': self.amount_different,
            'tax_ids': self.contract_id.vat_id.ids,
        })


    def _prepare_default_reversal(self, move):
        reverse_date = self.date
        mixed_payment_term = move.invoice_payment_term_id.id if move.invoice_payment_term_id and move.company_id.early_pay_discount_computation == 'mixed' else None
        return {
            'ref': self.invoice_number,
            'payment_reference': self.invoice_number,
            'invoice_denominator': self.invoice_denominator,
            'date': reverse_date,
            'invoice_date_due': reverse_date,
            'invoice_date': reverse_date or False,
            'journal_id': self.journal_id.id,
            'invoice_payment_term_id': mixed_payment_term,
            'invoice_user_id': move.invoice_user_id.id,
            'auto_post': 'no',
            'move_type': 'in_refund',
            'purchase_contract_id': self.contract_id.id,
        }

    def action_confirm(self):
        if self.contract_id.type == 'consign':
            if self.contract_id.invoice_ids:
                raise UserError(_("You already have invoice for this NPE"))
        if self.quantity > 0:
            remain_qty = self.contract_id.invoice_qty_remain
            if self.quantity > remain_qty:
                raise UserError(_("You cannot input quantity more than remain invoice quantity of contract"))
        if self.contract_id.type == 'purchase' and self.is_converted:
            price_contract = self.contract_id.relation_price_unit
            price_contact_npe = self.invoice_origin_id.price_unit
            if self.amount_different <= 0:
                raise UserError(_("Amount different must be greater than 0"))
            if price_contract > price_contact_npe:
                return self.create_debit()
            if price_contract < price_contact_npe:
                return self.create_credit()
        invoice = self.env['account.move']
        invoice_line = self.env['account.move.line']
        invoice_vals = {'name': 'Draft',
                        'origin': self.contract_id.name,
                        'partner_id': self.contract_id.partner_id.id,
                        'move_type': 'in_invoice',
                        'invoice_date': self.date or False,
                        'currency_id': self.contract_id.currency_id.id or False,
                        'narration': '',
                        'company_id': 1,
                        'user_id': self.env.uid,
                        'partner_bank_id': False,
                        'ref': self.invoice_number or False,
                        'reference_description': self.invoice_number or False,
                        'invoice_denominator': self.invoice_denominator or False,
                        'journal_id': self.journal_id.id or False,
                        'payment_reference': self.invoice_number or False,
                        'trans_type': 'local',
                        'purchase_contract_id': self.contract_id.id or False}

        invoice_id = invoice.create(invoice_vals)
        if self.contract_id.type in ['consign', 'ptbf']:
            for line in self.contract_id.contract_line:
                vals = self._prepare_invoice_line(line, invoice_id, invoice_vals, price_unit=self.price_unit)
                invoice_line.create(vals)
        if self.contract_id.type == 'purchase':
            for line in self.contract_id.contract_line:
                vals = self._prepare_invoice_line(line, invoice_id, invoice_vals, price_unit=line.price_unit)
                invoice_line.create(vals)
