# -*- encoding: utf-8 -*-
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
    date = fields.Date(string='Invoice Date')
    price_unit = fields.Float(string='Price Unit')
    paid_amount = fields.Float(string='Paid Amount')

    @api.model
    def default_get(self, fields):
        res = super(WizardCreateInvoice, self).default_get(fields)
        active_id = self.env.context.get('active_id')
        purchase_contract = self.env['purchase.contract'].browse(active_id)
        if purchase_contract:
            res['contract_id'] = purchase_contract.id
            res['quantity'] = purchase_contract.invoice_qty_remain
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


    def action_confirm(self):
        if self.contract_id.type == 'consign':
            if self.invoice_ids:
                raise UserError(_("You already have invoice for this NPE"))
        if self.quantity > 0:
            remain_qty = self.contract_id.invoice_qty_remain
            if self.quantity > remain_qty:
                raise UserError(_("You cannot input quantity more than remain invoice quantity of contract"))
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
