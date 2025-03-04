# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict
import re
DATE_FORMAT = "%Y-%m-%d"

class PurchaseReport(models.Model):
    _name = 'purchase.report'
    _description = 'Purchase Report'
    _auto = False

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
    gross_qty = fields.Float(string='Gross Qty')
    quality_deduction = fields.Float(string='Quality Deduction')
    net_qty = fields.Float(string='Net Qty')
    net_price = fields.Float(string='Net Price/kg')
    premium = fields.Float(string='Premium')
    gross_price = fields.Float(string='Gross Price/kg')
    gross_value = fields.Float(string='Gross Value')
    deduction_value = fields.Float(string='Deduction Value')
    net_value = fields.Float(string='Net Value')
    invoice_number = fields.Char(string='Invoice Number')
    invoice_date = fields.Date(string='Invoice Date')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'v_faq_prod')
        self.env.cr.execute("""
                    CREATE OR REPLACE VIEW public.purchase_report AS
                    select row_number() OVER (

                                ORDER BY (
                                    pc.id,
                                    sa.date_picking,
                                    sp.id,
                                    sa.date_picking,
                                    rp.partner_code,
                                    rp.id,
                                    rp.estate_name,
                                    pp.default_code,
                                    pp.id,
                                    sa.certificate_id,
                                    pc.crop_id,
                                    np.id
                                ) DESC  
            ) AS id, pc.id as purchase_contract_id, 
                             sa.date_picking as purchase_date, 
                             Null as consignment_id, 
                             Null as consignment_date, 
                             sp.id as picking_id,
                              sa.date_picking as grn_date, 
                              rp.partner_code as partner_code, 
                              rp.id as partner_id, 
                              rp.estate_name as estate_name,
                              pp.default_code as default_code, 
                              pp.id as product_id, 
                              sa.certificate_id as certificate_id,
                           pc.crop_id as crop_id, 
                           np.id as packing_id, 
                           sp.total_bag as total_bag,
                            sa.qty_allocation_net as gross_qty,
                             sp.deduction_qty as quality_deduction,
                              sa.qty_allocation as net_qty, 
                              pc.relation_price_unit as net_price, 
                              pc.premium as premium,
                               pc.gross_price as gross_price, 
                               sa.qty_allocation_net * pc.gross_price as gross_value,
                           sp.deduction_qty * pc.gross_price as deduction_value, 
                           sa.qty_allocation * pc.gross_price as net_value,
                           ipc.invoice_number as invoice_number,
                           ipc.invoice_date as invoice_date
                    from stock_allocation sa
                    join purchase_contract pc on sa.contract_id = pc.id
                    join stock_picking sp on sp.id = sa.picking_id
                    LEFT JOIN invoice_purchase_contract ipc on ipc.picking_id = sp.id
                    join res_partner rp on rp.id = sa.partner_id
                    join product_product pp on pp.id = sa.product_id
                    join ned_packing np on np.id = sp.packing_id
                    
                    where pc.type = 'purchase' and pc.origin is NULL;
""")