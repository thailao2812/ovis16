# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class AccountMove(models.Model):
    _inherit = 'account.move'

    purchase_contract_id = fields.Many2one('purchase.contract')
    purchase_contract_invoice_ids = fields.One2many('purchase.contract.invoice', 'move_id')

    allocated_untaxed_amount = fields.Float(string='Allocated Amount', compute='_compute_allocated_amount', store=True)
    allocated_taxed_amount = fields.Float(string='Allocated Amount', compute='_compute_allocated_amount', store=True)
    allocated_total_amount = fields.Float(string='Allocated Amount', compute='_compute_allocated_amount', store=True)
    remain_untaxed_amount = fields.Float(string='Remain Amount', compute='_compute_allocated_amount', store=True)
    remain_taxed_amount = fields.Float(string='Remain Amount', compute='_compute_allocated_amount', store=True)
    remain_total_amount = fields.Float(string='Remain Amount', compute='_compute_allocated_amount', store=True)
    total_quantity = fields.Float(string='Total Quantity', compute='_compute_total_quantity', store=True)
    remain_quantity = fields.Float(string='Remain Quantity', compute='_compute_total_quantity', store=True)

    @api.depends('purchase_contract_invoice_ids.quantity', 'purchase_contract_invoice_ids.amount_allocated_untaxed', 'purchase_contract_id',
                 'purchase_contract_id.state', 'purchase_contract_id.type', 'amount_untaxed', 'amount_tax', 'amount_total',
                 'purchase_contract_invoice_ids.amount_allocated_tax', 'purchase_contract_invoice_ids.amount_allocated_total')
    def _compute_allocated_amount(self):
        for rec in self:
            if rec.purchase_contract_id.type == 'consign':
                rec.allocated_untaxed_amount = sum(rec.purchase_contract_invoice_ids.mapped('amount_allocated_untaxed'))
                rec.allocated_taxed_amount = sum(rec.purchase_contract_invoice_ids.mapped('amount_allocated_tax'))
                rec.allocated_total_amount = sum(rec.purchase_contract_invoice_ids.mapped('amount_allocated_total'))
                rec.remain_untaxed_amount = rec.amount_untaxed - sum(rec.purchase_contract_invoice_ids.mapped('amount_allocated_untaxed'))
                rec.remain_taxed_amount =  rec.amount_tax - sum(rec.purchase_contract_invoice_ids.mapped('amount_allocated_tax'))
                rec.remain_total_amount = rec.amount_total - sum(rec.purchase_contract_invoice_ids.mapped('amount_allocated_total'))
            else:
                rec.allocated_untaxed_amount = 0
                rec.allocated_taxed_amount = 0
                rec.allocated_total_amount = 0
                rec.remain_untaxed_amount = 0
                rec.remain_taxed_amount = 0
                rec.remain_total_amount = 0

    @api.depends('purchase_contract_invoice_ids.quantity', 'invoice_line_ids', 'invoice_line_ids.quantity', 'purchase_contract_invoice_ids')
    def _compute_total_quantity(self):
        for rec in self:
            rec.total_quantity = sum(rec.invoice_line_ids.mapped('quantity'))
            rec.remain_quantity = rec.total_quantity - sum(rec.purchase_contract_invoice_ids.mapped('quantity'))

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
                # _affect_tax_report may trigger premature recompute of line_ids.date
                self.env.add_to_compute(move.line_ids._fields['date'], move.line_ids)
                # might be protected because `_get_accounting_date` requires the `name`
                # self.env.add_to_compute(self._fields['name'], move)

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def _compute_account_id(self):
        res = super(AccountMoveLine, self)._compute_account_id()
        product_lines = self.filtered(lambda line: line.display_type == 'product' and line.move_id.is_invoice(True))
        for line in product_lines:
            if line.product_id:
                fiscal_position = line.move_id.fiscal_position_id
                accounts = line.with_company(line.company_id).product_id \
                    .product_tmpl_id.get_product_accounts(fiscal_pos=fiscal_position)
                if line.move_id.is_sale_document(include_receipts=True):
                    line.account_id = accounts['income'] or line.account_id
                elif line.move_id.is_purchase_document(include_receipts=True):
                    if line.move_id.purchase_contract_id and self.env.user.company_id.stock_account_coffee_id:
                        line.account_id = self.env.user.company_id.stock_account_coffee_id.id
                    elif line.purchase_line_id and self.env.user.company_id.stock_account_consumable_id:
                        line.account_id = self.env.user.company_id.stock_account_consumable_id.id
                    else:
                        line.account_id = accounts['expense'] or line.account_id
        return res