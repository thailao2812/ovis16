
# -*- coding: utf-8 -*-
import logging, datetime, timeit
from datetime import timedelta
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SaleSubscriptionLine(models.Model):
    _inherit = 'sale.subscription.line'

    budget_item = fields.Many2one('account.analytic.account', string='Budget Item')
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")
    smp_discount = fields.Float(string='Smartpay Discount')
    tax_ids = fields.Many2many('account.tax', string='Tax(es)')
    product_updatable = fields.Boolean(compute='_compute_product_updatable', string='Can Edit Product', readonly=True, default=True)
    product_id = fields.Many2one('product.product', string='Product', domain="[('recurring_invoice','=',True)]", required=False)
    price_subtotal = fields.Float(compute='_compute_price_subtotal', string='Sub Total', digits=dp.get_precision('Account'), store=True)
    invoice_number = fields.Char(string='Invoice Number')
    invoice_date = fields.Date(string='Invoice Date')
    
    @api.depends('product_id', 'price_unit', 'uom_id')
    def _compute_product_updatable(self):
        for line in self:
            if line.analytic_account_id.stage_id == 1:
                line.product_updatable = False
            else:
                line.product_updatable = True

    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'uom_id' not  in vals:
                vals['uom_id'] = 1
            if 'price_unit' not  in vals:
                vals['price_unit'] = 1
        sale_subscription_line_ids = super(SaleSubscriptionLine, self).create(vals_list)
        return sale_subscription_line_ids
    
    @api.depends('price_unit', 'quantity', 'discount', 'analytic_account_id.pricelist_id', 'tax_ids')
    def _compute_price_subtotal(self):
        AccountTax = self.env['account.tax']
        for line in self:
            price = AccountTax._fix_tax_included_price(line.price_unit, line.sudo().tax_ids, AccountTax)
            line.price_subtotal = line.quantity * price * (100.0 - line.discount) / 100.0
            if line.analytic_account_id.pricelist_id.sudo().currency_id:
                line.price_subtotal = line.analytic_account_id.pricelist_id.sudo().currency_id.round(line.price_subtotal)
    
    def _smn_amount_line_tax(self):
        self.ensure_one()
        val = 0.0
        product = self.product_id
        for tax in self.tax_ids:
            if self.smp_discount > 0:
                compute_vals = tax.compute_all(self.price_unit * (self.smp_discount / 100.0), self.analytic_account_id.currency_id, self.quantity, product)['taxes']
            else:
                compute_vals = tax.compute_all(self.price_unit * (1 - (self.discount or 0.0) / 100.0), self.analytic_account_id.currency_id, self.quantity, product)['taxes']
            if compute_vals:
                val += compute_vals[0].get('amount', 0)
        return val