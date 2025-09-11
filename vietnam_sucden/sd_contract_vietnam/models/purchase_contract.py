# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class PurchaseContract(models.Model):
    _inherit = 'purchase.contract'

    list_farmer = fields.One2many('list.farmer', 'purchase_contract_id')

    equiv_faq_price = fields.Float(string='Equiv. FAQ price', related='contract_line.equiv_faq_price', store=True)

    deposit_amount = fields.Float(string='Deposit Amount')

    print_company = fields.Boolean(string='Print Company Name')

    open_qty = fields.Float(string='No Payment Qty')

    list_open_qty = fields.One2many('open.qty.npe', 'purchase_contract_id')

    user_approve = fields.Many2one('res.users', string='User Approve', readonly=False, domain=[('trader', '=', True)])

    percent_advance_price = fields.Integer(string="Percent Advance Price", default=70)

    license_2nd_id = fields.Many2one('ned.certificate.license', string='IB License')

    according_final_payment_id = fields.Many2one('purchase.contract.according', string='According Final Payment')

    invoice_lines_ids = fields.One2many('purchase.invoice.line', 'purchase_contract_id')

    state_final_payment = fields.Selection([
        ('draft', 'Draft'),
        ('request', 'Request'),
        ('approve', 'Approve'),
        ('director', 'Director'),
        ('paid', 'Paid'),
    ], string='Final Payment State', default='draft', tracking=True)

    state = fields.Selection(tracking=True)

    partner_invoice_id = fields.Many2one(required=False)
    partner_shipping_id = fields.Many2one(required=False)

    offset_debt_ids = fields.One2many('offset.debt', 'purchase_contract_id')

    diff_price = fields.Float(tracking=True)

    provisional_price = fields.Float(string='Provisional Price')

    invoice_qty = fields.Float(string="Invoice Qty", compute='_compute_invoice_qty', store=True, digits=(16,0))
    invoice_qty_remain = fields.Float(string="Invoice Qty Remain", compute='_compute_invoice_qty', store=True, digits=(16,0))

    invoice_ids = fields.One2many('account.move', 'purchase_contract_id', string='Invoice')
    vat_id = fields.Many2one('account.tax', string='VAT', related='contract_line.vat_id', store=True)

    invoice_amount = fields.Float(string='Invoice Paid Amount', compute='_amount_all', store=True)
    different_amount = fields.Float(string='Different Amount', compute='_amount_all', store=True)

    purchase_contract_invoice_ids = fields.One2many('purchase.contract.invoice', 'purchase_contract_id')

    invoice_price = fields.Float(string='Invoice Price', compute='_compute_invoice_price', store=True)
    have_invoice_adjust = fields.Boolean(string='Have Invoice Adjustment?', compute='_compute_invoice_adjustment', store=True)

    total_pay_goods = fields.Float(string='Total Pay Goods', compute='_amount_all', store=True)


    @api.depends('invoice_ids', 'invoice_ids.state', 'invoice_ids.total_qty',
                 'state', 'total_qty', 'origin', 'purchase_contract_invoice_ids')
    def _compute_invoice_adjustment(self):
        for record in self:
            if record.origin or record.purchase_contract_invoice_ids:
                if not record.invoice_ids:
                    record.have_invoice_adjust = False
                else:
                    record.have_invoice_adjust = True

    @api.depends('invoice_ids', 'invoice_ids.state', 'type', 'state')
    def _compute_invoice_price(self):
        for record in self:
            if record.type == 'consign':
                if record.invoice_ids:
                    record.invoice_price = record.invoice_ids[0].price_unit
                else:
                    record.invoice_price = 0
            else:
                record.invoice_price = 0

    @api.depends('invoice_ids', 'invoice_ids.state', 'invoice_ids.total_qty', 'state', 'total_qty', 'origin', 'purchase_contract_invoice_ids')
    def _compute_invoice_qty(self):
        for record in self:
            if record.purchase_contract_invoice_ids:
                record.invoice_qty = sum(record.purchase_contract_invoice_ids.mapped('quantity'))
                record.invoice_qty_remain = 0
            else:
                record.invoice_qty = sum(record.invoice_ids.filtered(lambda x: x.state != 'cancel' and x.move_type != 'in_refund').mapped('total_qty'))
                record.invoice_qty_remain = record.total_qty - sum(record.invoice_ids.filtered(lambda x: x.state != 'cancel' and x.move_type != 'in_refund').mapped('total_qty'))

    def button_request_final_payment(self):
        for record in self:
            record.state_final_payment = 'request'

    def button_approve_final_payment(self):
        for record in self:
            record.state_final_payment = 'approve'

    def button_approve_director_final_payment(self):
        for record in self:
            record.state_final_payment = 'director'

    def button_paid_final_payment(self):
        for record in self:
            payment = self.env['account.payment'].search([
                ('purchase_contract_id', '=', record.id),
                ('is_final_payment', '=', True),
                ('state', 'not in', ['posted', 'cancel']),
            ], limit=1)
            if payment:
                raise UserError(_("Looks like your final payment is chilling in the ‘to-do’ list. Time to give it a little nudge and check it off!"))
            return record.action_request_register_payment()

    def action_request_register_payment(self):
        return {
            'name': _('Register Payment'),
            'res_model': 'account.payment',
            'view_mode': 'form',
            # 'domain':self.request_payment_ids.ids,
            'context': {
                'active_model': 'purchase.contract',
                'active_ids': self.ids,
                'final_payment': True,
                'default_partner_type': 'supplier',
                'default_is_final_payment': True
                # 'currency_id':
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def print_final_payment(self):
        return self.env.ref('sd_contract_vietnam.report_final_payment_purchase_contract').report_action(self)

    def print_nvp_npe(self):
        return self.env.ref('sd_contract_vietnam.report_nvp_npe_contact').report_action(self)

    def print_nvp_word(self):
        return self.env.ref('sd_contract_vietnam.report_nvp_word').report_action(self)

    def print_npe_word(self):
        return self.env.ref('sd_contract_vietnam.report_nve_word').report_action(self)

    def print_nvp_npe_word(self):
        return self.env.ref('sd_contract_vietnam.report_nvp_npe_contact_word').report_action(self)

    def print_ptbf_word(self):
        if self.nvp_ids:
            return self.env.ref(
                'sd_contract_vietnam.report_ptbf_npe_word').report_action(self)

        else:
            return self.env.ref(
                'sd_contract_vietnam.report_ptbf_word').report_action(self)

    def action_force_close_npe(self):
        return {
            'name': _('Force Close NPE'),
            'res_model': 'force.close.npe',
            'view_mode': 'form',
            'context': {
                'active_model': 'purchase.contract',
                'res_id': self.id,
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    @api.depends('contract_line.price_total', 'contract_line.price_unit', 'pay_allocation_ids',
                 'pay_allocation_ids.allocation_amount',
                 'request_payment_ids', 'request_payment_ids.total_payment', 'payment_ids', 'payment_ids.amount',
                 'stock_allocation_ids', 'type', 'npe_ids', 'nvp_ids',
                 'stock_allocation_ids.qty_allocation',
                 'pay_allocation_ids.allocation_line_ids', 'purchase_contract_invoice_ids', 'purchase_contract_invoice_ids.quantity',
                 'purchase_contract_invoice_ids.amount_allocated_untaxed', 'purchase_contract_invoice_ids.amount_allocated_tax',
                 'purchase_contract_invoice_ids.amount_allocated_total',
                 'ptbf_ids', 'state', 'total_qty', 'vat_id', 'provisional_price', 'invoice_ids', 'invoice_qty', 'invoice_qty_remain',
                 'invoice_ids.state', 'invoice_ids.payment_state', 'ptbf_ids.history_rate_ids.total_amount_vn', 'offset_debt_ids', 'offset_debt_ids.amount')
    def _amount_all(self):
        for contract in self:
            price_unit = 0.0
            amount_untaxed = 0
            amount_tax = 0.0
            tax_id = contract.vat_id
            amount = 0.0
            amount_deposit = 0.0
            sub_rel = 0.0
            invoice_ids = self.invoice_ids.filtered(lambda x: x.state == 'posted' and x.payment_state in ['paid', 'partial'])
            amount_payment = 0
            for move in invoice_ids:
                if move.state == 'posted' and move.is_invoice(include_receipts=True):
                    reconciled_partials = move._get_all_reconciled_invoice_partials()
                    for reconciled_partial in reconciled_partials:
                        counterpart_line = reconciled_partial['aml']
                        payment_id = counterpart_line.payment_id
                        amount_payment += payment_id.amount
            contract.invoice_amount = amount_payment

            if contract.type == 'ptbf':
                amount_untaxed = 0
                for i in contract.ptbf_ids:
                    for j in i.history_rate_ids:
                        amount_untaxed += j.total_amount_vn
                amount_tax = amount_untaxed * (tax_id.amount/100)

            if contract.type == 'consign':
                total_qty = contract.total_qty
                provisional_price = price_unit = contract.provisional_price
                amount_untaxed = total_qty * provisional_price
                amount_tax = amount_untaxed * (tax_id.amount/100)
            if contract.type == 'purchase':
                for line in contract.contract_line:
                    amount_untaxed += line.price_subtotal
                    price_unit = line.price_unit

                amount_tax = amount_untaxed * (tax_id.amount/100)

            if not contract.nvp_ids:
                for stock in contract.stock_allocation_ids:
                    sub_rel += stock.qty_allocation
            else:
                for alls in contract.contract_line:
                    sub_rel += alls.product_qty
            if contract.type != 'ptbf':
                sub_rel = sub_rel * price_unit
            else:
                sub_rel = amount_untaxed

            for deposit in contract.pay_allocation_ids:
                amount_deposit += deposit.allocation_amount or 0.0
                for interest in deposit.allocation_line_ids:
                    amount += interest.actual_interest_pay

            for deposit in contract.payment_ids.filtered(lambda x: x.state == 'posted'):
                amount_deposit += deposit.amount

            amount = abs(amount) * (-1)
            amount_deposit = abs(amount_deposit) * (-1)
            contract.update({
                'amount_untaxed': contract.currency_id.round(amount_untaxed),
                'amount_tax': contract.currency_id.round(amount_tax),
                'amount_sub_total': amount_untaxed + amount_tax,
                'amount_total': sub_rel + amount + amount_deposit - sum(contract.offset_debt_ids.mapped('amount')) + amount_tax,
                'total_pay_goods': sub_rel + amount + amount_deposit - sum(contract.offset_debt_ids.mapped('amount')),
                'amount_sub_rel_total': sub_rel,
                'total_interest_pay': abs(amount),
                'amount_deposit': abs(amount_deposit)
            })
            if contract.type == 'consign':
                contract.amount_total = amount_untaxed + amount_tax + amount_deposit
                contract.different_amount = contract.amount_total - contract.invoice_amount

    def create_invoice_adjustment(self):
        print(123)


class OpenQtyNPE(models.Model):
    _name = 'open.qty.npe'

    purchase_contract_id = fields.Many2one('purchase.contract')
    contract_id = fields.Many2one('purchase.contract', string='NPE')
    qty = fields.Float(string='')

class PurchaseInvoiceLine(models.Model):
    _name = 'purchase.invoice.line'

    purchase_contract_id = fields.Many2one('purchase.contract')
    name = fields.Char(string='Invoice No.')
    invoice_date = fields.Date(string='Invoice Date')
    quantity = fields.Float(string='Invoice Quantity')
    price_unit = fields.Float(string='Invoice Price')
    total_amount = fields.Float(string='Total Amount Untax', compute='compute_total_amount', store=True)
    tax = fields.Float(string='Tax Amount')
    total_amount_tax = fields.Float(string='Total Amount', compute='compute_total_amount', store=True)

    @api.depends('quantity', 'price_unit', 'tax')
    def compute_total_amount(self):
        for rec in self:
            rec.total_amount = rec.price_unit * rec.quantity
            rec.total_amount_tax = (rec.price_unit * rec.quantity) + rec.tax

