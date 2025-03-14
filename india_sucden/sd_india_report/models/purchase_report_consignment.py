# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict
import re
DATE_FORMAT = "%Y-%m-%d"

class PurchaseReportConsignment(models.Model):
    _name = 'purchase.report.consignment'
    _description = 'Purchase Report Consignment'

    purchase_contract_id = fields.Many2one('purchase.contract', string='Pur. Contract No')
    purchase_date = fields.Date(string='Purchase Date')
    consignment_id = fields.Many2one('purchase.contract', string='CS No')
    consignment_date = fields.Date(string='Consignment Date')
    picking_id = fields.Many2one('stock.picking', string='GRN No.')
    grn_date = fields.Date(string='GRN Date')
    partner_code = fields.Char(string='Vendor Code')
    partner_id = fields.Many2one('res.partner', string='Vendor Name')
    estate_name = fields.Char(string='Estate Name')
    default_code = fields.Char(string='Item Code')
    product_id = fields.Many2one('product.product', string='Item Name')
    certificate_id = fields.Many2one('ned.certificate', string='Certificate')
    crop_id = fields.Many2one('ned.crop', string='Crop Season')
    packing_id = fields.Many2one('ned.packing', string='Packing Mode')
    total_bag = fields.Float(string='No of Bag')
    gross_qty = fields.Float(string='Gross Qty')  # CR Contract
    quality_deduction = fields.Float(string='Quality Deduction') # CR Contract
    net_qty = fields.Float(string='Net Qty') # calculation
    net_price = fields.Float(string='Net Price/kg') # CR contract
    premium = fields.Float(string='Premium') # CR contract
    gross_price = fields.Float(string='Gross Price/kg') # calculation
    gross_value = fields.Float(string='Gross Value') # calculation
    deduction_value = fields.Float(string='Deduction Value') # calculation
    net_value = fields.Float(string='Net Value') # calculation
    invoice_number = fields.Char(string='Invoice Number') # CR contract
    invoice_date = fields.Date(string='Invoice Date') # CR contract

    @api.model
    def cron_action_create_purchase_report_consignment(self):
        self.env.cr.execute("DELETE FROM purchase_report_consignment")

        stock_allocation = self.env['stock.allocation'].search([
            ('contract_id.type', '=', 'consign'),
        ])
        for stock in stock_allocation:
            value = {
                'consignment_id': stock.contract_id.id,
                'consignment_date': stock.contract_id.date_order,
                'picking_id': stock.picking_id.id,
                'grn_date': stock.picking_id.date_done,
                'partner_code': stock.partner_id.partner_code,
                'partner_id': stock.partner_id.id,
                'estate_name': stock.partner_id.estate_name,
                'default_code': stock.product_id.default_code,
                'product_id': stock.product_id.id,
                'certificate_id': stock.contract_id.certificate_id.id,
                'crop_id': stock.contract_id.crop_id.id,
                'packing_id': stock.contract_id.packing_id.id,
                'total_bag': stock.picking_id.total_bag,
            }
            contract_cs = stock.contract_id
            for cr in contract_cs.npe_ids.mapped('contract_id'):
                invoice_number = self.env['invoice.purchase.contract'].search([
                    ('contract_id', '=', cr.id),
                ], limit=1)
                value.update({
                    'purchase_contract_id': cr.id,
                    'purchase_date': cr.date_order,
                    'gross_qty': cr.gross_qty,
                    'quality_deduction': cr.quality_deduction,
                    'net_qty': cr.gross_qty - cr.quality_deduction,
                    'net_price': cr.relation_price_unit,
                    'premium': cr.premium,
                    'gross_price': cr.relation_price_unit + cr.premium,
                    'gross_value': cr.gross_qty * (cr.relation_price_unit + cr.premium),
                    'deduction_value': cr.quality_deduction * (cr.relation_price_unit + cr.premium),
                    'net_value': (cr.gross_qty - cr.quality_deduction) * (cr.relation_price_unit + cr.premium),
                    'invoice_number': invoice_number.invoice_number if invoice_number else False,
                    'invoice_date': invoice_number.invoice_date if invoice_number else False,
                })
                self.env['purchase.report.consignment'].create(value)