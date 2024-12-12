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

    partner_invoice_id = fields.Many2one(required=False)
    partner_shipping_id = fields.Many2one(required=False)

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
                raise UserError(_("🚀 Uh-oh! Looks like your final payment is chilling in the ‘to-do’ list. 🛋️ Time to give it a little nudge and check it off! ✅💸✨"))
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

