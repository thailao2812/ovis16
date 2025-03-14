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
                 'stock_allocation_ids',
                 'stock_allocation_ids.qty_allocation',
                 'pay_allocation_ids.allocation_line_ids',
                 'ptbf_ids', 'state',
                 'ptbf_ids.history_rate_ids.total_amount_vn', 'offset_debt_ids', 'offset_debt_ids.amount')
    def _amount_all(self):
        for contract in self:
            price_unit = 0.0
            amount_untaxed = 0
            amount_tax = 0.0

            amount = 0.0
            amount_deposit = 0.0
            sub_rel = 0.0

            if contract.type == 'ptbf':
                amount_untaxed = 0
                for i in contract.ptbf_ids:
                    for j in i.history_rate_ids:
                        amount_untaxed += j.total_amount_vn
                        amount_tax = 0

            else:
                for line in contract.contract_line:
                    amount_untaxed += line.price_subtotal
                    amount_tax += line.price_tax
                    price_unit = line.price_unit

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
                'amount_total': sub_rel + amount + amount_deposit - sum(contract.offset_debt_ids.mapped('amount')),
                'amount_sub_rel_total': sub_rel,
                'total_interest_pay': abs(amount),
                'amount_deposit': abs(amount_deposit)
            })


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

