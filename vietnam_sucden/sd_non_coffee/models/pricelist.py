# -*- encoding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID
import datetime
import time
import pytz
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

class ProductSupplierParent(models.Model):
    _name = 'product.supplier.parent'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Vendor Pricelists"

    name  = fields.Char(string='Name', size=128)
    notes = fields.Text(string='Other Term')
    valid_from = fields.Date(string='Valid From')
    valid_to   = fields.Date(string='Valid To')
    warranty   = fields.Char(string='Warranty', size=128)
    partner_id = fields.Many2one('res.partner', string='Vendor')
    child_ids  = fields.One2many('product.supplierinfo', 'parent_id', string='Pricelist Items')
    delivery_time   = fields.Integer(string='Vendor Lead Time')
    currency_id     = fields.Many2one('res.currency', string='Currency')
    delivery_cost   = fields.Many2one('delivery.carrier', string='Carrier')
    payment_term_id = fields.Many2one('account.payment.term', 'Payment Term')
    
    state = fields.Selection(selection=[
        ('draft', "Draft"),
        ('confirm', "Confirmed"),
        ('approve', "Approved"),
    ], string="Status",readonly=True, copy=False, index=True,tracking=True,default='draft')

    def action_confirm(self):
        return self.write({'state': 'confirm'})
    
    def action_verify(self):
        return self.write({'state': 'approve'})

class ProductSupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    parent_id = fields.Many2one('product.supplier.parent', 'Parent')
    sequence  = fields.Integer(string="Sequence", default=10)
    tax_ids = fields.Many2many('account.tax', 'item_taxes_rel', 'item_id', 'tax_id', 'VAT(%)')
