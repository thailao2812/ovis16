# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class AccountMove(models.Model):
    _inherit = 'account.move'

    purchase_contract_id = fields.Many2one('purchase.contract')
    purchase_contract_invoice_ids = fields.One2many('purchase.contract.invoice', 'move_id')
    user_approve = fields.Many2one('res.users', string='Approve By', compute='_compute_user_approve', store=True,
                                   readonly=True, states={'draft': [('readonly', False)]})
    invoice_denominator = fields.Char(string='Invoice Denominator')

    allocated_untaxed_amount = fields.Float(string='Allocated Untaxed Amount', compute='_compute_allocated_amount', store=True)
    allocated_taxed_amount = fields.Float(string='Allocated Tax Amount', compute='_compute_allocated_amount', store=True)
    allocated_total_amount = fields.Float(string='Allocated Total Amount', compute='_compute_allocated_amount', store=True)
    remain_untaxed_amount = fields.Float(string='Remain Untaxed Amount', compute='_compute_allocated_amount', store=True)
    remain_taxed_amount = fields.Float(string='Remain Tax Amount', compute='_compute_allocated_amount', store=True)
    remain_total_amount = fields.Float(string='Remain Total Amount', compute='_compute_allocated_amount', store=True)
    total_quantity = fields.Float(string='Total Quantity', compute='_compute_total_quantity', store=True)
    remain_quantity = fields.Float(string='Remain Quantity', compute='_compute_total_quantity', store=True)
    stock_picking_ids = fields.One2many('stock.picking.allocated', 'invoice_id', string='Stock Picking')
    total_allocated_amount = fields.Integer(string='Total Allocated Amount by GRN', compute='_compute_total_allocated_amount', store=True)
    check = fields.Boolean(string='Check', compute='_compute_total_allocated_amount', store=True, default=False)

    attachment_ids = fields.Many2many('ir.attachment', 'account_move_attachment_rel', 'move_id',
                                      'attachment_id', 'Attachments')

    @api.depends('stock_picking_ids.allocated_amount')
    def _compute_total_allocated_amount(self):
        for rec in self:
            rec.total_allocated_amount = sum(rec.stock_picking_ids.mapped('allocated_amount'))
            if rec.total_allocated_amount == rec.total_quantity:
                rec.check = True

    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('approved', 'Approved'),
            ('posted', 'Posted'),
            ('cancel', 'Cancelled'),
        ],
        string='Status',
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
        default='draft',
    )

    price_unit = fields.Float(string='Price Unit', related='invoice_line_ids.price_unit', store=True)
    product_id = fields.Many2one('product.product', related='invoice_line_ids.product_id', store=True)

    history_rate_id = fields.Many2one('history.rate')
    ptbf_fixprice_id = fields.Many2one('ptbf.fixprice')

    @api.depends('purchase_contract_id')
    def _compute_user_approve(self):
        for rec in self:
            rec.user_approve = False
            if rec.purchase_contract_id:
                rec.user_approve = rec.purchase_contract_id.user_approve.id if rec.purchase_contract_id.user_approve else False

    @api.depends('purchase_contract_invoice_ids.quantity', 'purchase_contract_invoice_ids.amount_allocated_untaxed', 'purchase_contract_id',
                 'purchase_contract_id.state', 'purchase_contract_id.type', 'amount_untaxed', 'amount_tax', 'amount_total',
                 'purchase_contract_invoice_ids.amount_allocated_tax', 'purchase_contract_invoice_ids.amount_allocated_total')
    def _compute_allocated_amount(self):
        return True

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

    def name_get(self):
        result = []
        for rec in self:
            if rec.purchase_contract_id:
                name = rec.purchase_contract_id.name + "/"+ rec.name
                result.append((rec.id, name))
            else:
                result.append((rec.id, rec.name))
        return result

    def action_approve(self):
        for rec in self:
            if rec.move_type != 'out_invoice':
                if self.env.uid != rec.user_approve.id:
                    raise UserError(_('You cannot approve this Invoice. Please select another person in your team.'))
            rec.state = 'approved'

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('You cannot delete invoice.'))
        invoice = super(AccountMove, self).unlink()
        return invoice

    @api.constrains('line_ids', 'fiscal_position_id', 'company_id')
    def _validate_taxes_country(self):
        return True

    def action_mapping_grn(self):
        action = self.env.ref('sd_contract_vietnam.action_mapping_grn_invoice').read()[0]
        return action

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

class StockPickingAllocated(models.Model):
    _name = 'stock.picking.allocated'

    invoice_id = fields.Many2one('account.move', string='Invoice')
    picking_id = fields.Many2one('stock.picking', string='Picking')
    contract_id = fields.Many2one('purchase.contract', string='Purchase Contract')
    allocated_qty = fields.Integer(string='Allocated Quantity')
    allocated_amount = fields.Integer(string='Input Allocated Invoice')