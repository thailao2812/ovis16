# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict
import re
DATE_FORMAT = "%Y-%m-%d"

class LotAllocationBonded(models.Model):
    _name = 'v.lot.allocation.bonded'
    _description = 'Lot Allocation Bonded'
    _auto = False
    
    name = fields.Char(string = 'S-P Allocation')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    partner_id = fields.Many2one('res.partner', string='Buyer')
    shipment_date = fields.Char(string = 'Shipment Month')
    shipment_no = fields.Many2one('shipping.instruction', string='Shipment No.')
    p_contract_id = fields.Many2one('s.contract', string='P Contract')
    stack_id = fields.Many2one('stock.lot', string='Stack No.')
    wr_no = fields.Char(string = 'WR No.')
    real_stack_export = fields.Char(string = 'Real Stack Export')
    shipper_id = fields.Many2one('res.partner', string='Shipper')
    product_id = fields.Many2one('product.product', string='Product')
    quality = fields.Char(string='Quality')
    gdn_name = fields.Char(string='GDN No.')
    scertificate_id = fields.Many2one('ned.certificate', string='Certificate')
    p_qty = fields.Float(string = 'P Qty', digits=(12, 0))
    allocate_qty = fields.Float(string = 'Allocate Qty', digits=(12, 0))
    bag_allocate = fields.Float(string = 'Bag Allocate', digits=(12, 0))
    balance_qty = fields.Float(string = 'Balance Qty', digits=(12, 0))
    balance_bag = fields.Float(string = 'Balance Bags', digits=(12, 0))
    mc_on_despatch = fields.Float(string = 'Mc On Despatch')
    real_qty = fields.Float(string = 'Real Qty', digits=(12, 0))
    inspection_qty = fields.Float(string = 'Inspection Qty', digits=(12, 0))
    state = fields.Selection([('draft', 'Draft'), ('approve', 'Approve')], string='Status')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'v_lot_allocation_bonded')
        self.env.cr.execute("""
                    CREATE OR REPLACE VIEW public.v_lot_allocation_bonded AS
                    SELECT row_number() OVER (ORDER BY (sc.id, scd.warehouse_id) DESC) AS id, 
                        sc.name, scd.warehouse_id, sc.shipment_date, sc.id AS shipment_no, scd.p_contract_id, 
                        scd.stack_id, scd.code_stack AS wr_no, scd.stack_on_hand AS real_stack_export, 
                        scd.shipper_id, sc.product_id, scd.name AS quality, sp.name AS gdn_name, 
                        scd.scertificate_id, sctr.p_qty, scd.tobe_qty AS allocate_qty, sc.partner_id,
                        scd.tobe_bag AS bag_allocate, scd.balance_qty, scd.x_bag_qty AS balance_bag, scd.mc_on_despatch,
                        scd.allocated_qty AS real_qty, scd.x_gd_qty AS inspection_qty, scd.state
                        FROM sale_contract_deatail scd
                        JOIN sale_contract sc ON sc.id=scd.sp_id
                        JOIN s_contract sctr ON sctr.id=scd.p_contract_id
                        JOIN stock_picking sp ON sp.id=sc.picking_id
                    """)