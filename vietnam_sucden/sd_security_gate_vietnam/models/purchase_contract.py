
# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
import math
from datetime import datetime, date, timedelta
import math


class PurchaseContract(models.Model):
    _inherit = 'purchase.contract'

    code_partner = fields.Char(string='Partner Code', related='partner_id.partner_code', store=True)
    stop_loss_price = fields.Float(string='Stop Loss %')
    date_fix_for_advance = fields.Integer(string='Time Fix')

    note_by_security_gate = fields.Text(string='Note Security Gate')

    stop_loss_value = fields.Float(string='Stop Loss Price', compute='_compute_stop_loss_value', store=True)

    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=False, readonly=True,
                                   states={}, default=False, related='delivery_place_id.warehouse_id', store=True)
    diff_price = fields.Float(compute='_get_diff_price', string='Diff.', store=True, readonly=False)
    total_tax_payable = fields.Float(string='Total Tax Payable', compute='_compute_all_tax', store=True)

    @api.depends('invoice_ids', 'invoice_ids.state', 'invoice_ids.amount_tax', 'request_payment_ids',
                 'request_payment_ids.state',
                 'request_payment_ids.request_amount', 'request_payment_ids.payment_tax')
    def _compute_all_tax(self):
        for record in self:
            total_payment_tax = sum(
                record.request_payment_ids.filtered(lambda x: x.state == 'paid' and x.payment_tax).mapped(
                    'request_amount'))
            record.total_tax_payable = sum(
                record.invoice_ids.filtered(lambda x: x.state != 'cancel').mapped('amount_tax')) - total_payment_tax

    @api.depends('stop_loss_price', 'total_advance', 'type', 'request_payment_ids', 'request_payment_ids.payment_quantity', 'request_payment_ids.state')
    def _compute_stop_loss_value(self):
        for rec in self:
            if rec.type == 'consign':
                total_payment_qty = sum(rec.request_payment_ids.mapped('payment_quantity'))
                if total_payment_qty > 0:
                    rec.stop_loss_value = ((rec.total_advance / total_payment_qty) * rec.stop_loss_price)/ 100
                else:
                    rec.stop_loss_value = 0
            else:
                rec.stop_loss_value = 0

    @api.depends('request_payment_ids', 'request_payment_ids.type', 'type',
                 'request_payment_ids.type_of_ptbf_payment', 'request_payment_ids.request_amount')
    def _compute_advance_amount(self):
        for line in self:
            amount = 0.0
            if line.type == 'ptbf':
                for i in line.request_payment_ids:
                    if i.type_of_ptbf_payment == 'advance':
                        amount += i.request_amount or 0.0
                line.advance_amount = amount