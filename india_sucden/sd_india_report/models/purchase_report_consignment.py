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
        # Clear existing data with direct SQL query
        self.env.cr.execute("DELETE FROM purchase_report_consignment")

        # Fetch all consignment stock allocations in a single query
        stock_allocations = self.env['stock.allocation'].search([
            ('contract_id.type', '=', 'consign'),
        ])

        # Prefetch related records to reduce database queries
        contract_ids = stock_allocations.mapped('contract_id')

        # Create a dictionary of invoice numbers keyed by contract_id for faster lookups
        contract_invoice_map = {}
        all_npe_contract_ids = contract_ids.mapped('npe_ids.contract_id')
        invoice_purchases = self.env['invoice.purchase.contract'].search([
            ('contract_id', 'in', all_npe_contract_ids.ids),
        ])

        for invoice in invoice_purchases:
            if invoice.contract_id.id not in contract_invoice_map:
                contract_invoice_map[invoice.contract_id.id] = {
                    'invoice_number': invoice.invoice_number,
                    'invoice_date': invoice.invoice_date
                }

        # Prepare values for bulk creation
        report_values = []

        for stock in stock_allocations:
            contract_cs = stock.contract_id

            # Base values common to all records for this stock allocation
            base_value = {
                'consignment_id': contract_cs.id,
                'consignment_date': contract_cs.date_order,
                'picking_id': stock.picking_id.id,
                'grn_date': stock.picking_id.date_done,
                'partner_code': stock.partner_id.partner_code,
                'partner_id': stock.partner_id.id,
                'estate_name': stock.partner_id.estate_name,
                'default_code': stock.product_id.default_code,
                'product_id': stock.product_id.id,
                'certificate_id': contract_cs.certificate_id.id,
                'crop_id': contract_cs.crop_id.id,
                'packing_id': contract_cs.packing_id.id,
                'total_bag': stock.picking_id.total_bag,
            }

            # Process each related purchase contract
            for cr in contract_cs.npe_ids.mapped('contract_id'):
                value = dict(base_value)  # Create a copy of base values

                # Calculate values once to avoid repeated calculations
                gross_qty = cr.gross_qty
                quality_deduction = cr.quality_deduction
                net_qty = gross_qty - quality_deduction
                relation_price_unit = cr.relation_price_unit
                premium = cr.premium
                gross_price = relation_price_unit + premium

                # Get invoice information from the map
                invoice_info = contract_invoice_map.get(cr.id, {})

                value.update({
                    'purchase_contract_id': cr.id,
                    'purchase_date': cr.date_order,
                    'gross_qty': gross_qty,
                    'quality_deduction': quality_deduction,
                    'net_qty': net_qty,
                    'net_price': relation_price_unit,
                    'premium': premium,
                    'gross_price': gross_price,
                    'gross_value': gross_qty * gross_price,
                    'deduction_value': quality_deduction * gross_price,
                    'net_value': net_qty * gross_price,
                    'invoice_number': invoice_info.get('invoice_number', False),
                    'invoice_date': invoice_info.get('invoice_date', False),
                })

                report_values.append(value)

        # Create all records in a single operation
        if report_values:
            self.env['purchase.report.consignment'].create(report_values)