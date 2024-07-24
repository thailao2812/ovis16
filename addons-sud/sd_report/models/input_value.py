# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict
import re
DATE_FORMAT = "%Y-%m-%d"

class Input_value(models.Model):
    _name = 'v.input.value'
    _description = 'Input value'
    _auto = False

    date_finished = fields.Date(string = 'MRP Date')
    batch_name = fields.Char(string = 'Batch No.')
    stack_name = fields.Char(string = 'Stack')
    itr = fields.Char(string = 'ITR/GRN')
    grn = fields.Char(string = 'GRN Branch')
    deduction = fields.Float(string = 'Qty. deduction', digits=(12, 2))
    origin = fields.Char(string = 'Origin')
    contract = fields.Char(string = 'Contract')
    date_order = fields.Date(string = 'Date Order')
    qty_allocation = fields.Float(string = 'Allocated Qty (Kg)', digits=(12, 0))
    # allocated_qty = fields.Float(string = 'SP Allocated Qty', digits=(12, 0))
    # qty_available = fields.Float(string = 'SP Qty Available', digits=(12, 0))
    # total_qty = fields.Float(string = 'Total Qty', digits=(12, 0))
    # total_init_qty = fields.Float(string = 'Total init', digits=(12, 0))
    total_bag = fields.Float(string = 'Bags Total', digits=(12, 0))
    vehicle_no = fields.Char(string = 'Vehicle No.')
    contract_price = fields.Float(string = 'Contrac Price', digits=(12, 0))
    commrate = fields.Float(string = 'Commercialrate', digits=(12, 0))

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
                    CREATE OR REPLACE VIEW public.v_input_value AS
                      SELECT row_number() OVER (ORDER BY find_grn.date_finished DESC) AS id,
                        find_grn.*, rkl.deduction, sa.qty_allocation, pc.name AS contract, pc.date_order, 
                        pcl.price_unit AS contract_price, rdis.name AS origin, mk.commercialrate as commrate
                        FROM ((select distinct mrp.name as batch_name, mrp.date_finished, ss_fac.name as stack_name, itr_fac.name as itr, grn_fac.name grn,
                        CASE WHEN grn_fac.total_bag IS NULL OR grn_fac.total_bag=0 THEN itr_fac.total_bag ELSE grn_fac.total_bag END AS total_bag,
                        CASE WHEN grn_fac.vehicle_no IS NULL THEN itr_fac.vehicle_no ELSE grn_fac.vehicle_no END AS vehicle_no,
                        CASE WHEN grn_fac.districts_id IS NULL THEN itr_fac.districts_id ELSE grn_fac.districts_id END AS districts_id,
                        CASE WHEN grn_fac.id IS NULL THEN itr_fac.id ELSE grn_fac.id END AS sp_id
                      from mrp_production mrp
                        join stock_picking gip on gip.production_id = mrp.id
                        join stock_picking_type spt_gip on gip.picking_type_id = spt_gip.id
                        join stock_lot ss_fac on gip.lot_id = ss_fac.id
                        join stock_picking itr_fac on itr_fac.lot_id = ss_fac.id
                        join stock_picking_type spt_itr on itr_fac.picking_type_id = spt_itr.id
                        LEFT join stock_picking grn_fac on grn_fac.id = itr_fac.backorder_id
                      where spt_gip.code='production_out' --AND mrp.state='done' AND mrp.name like '' 
                        AND spt_itr.code = 'incoming' 
                        AND mrp.state='done' AND grn_fac.lot_id IS NULL Order By ss_fac.name)
                      UNION ALL
                      (select distinct mrp.name as batch_name, mrp.date_finished, ss_bc.name as stack_name, itr_bc.name as itr, grn_bc.name grn,
                        CASE WHEN grn_bc.total_bag IS NULL OR grn_bc.total_bag=0 THEN itr_bc.total_bag ELSE grn_bc.total_bag END AS total_bag,
                        CASE WHEN grn_bc.vehicle_no IS NULL THEN itr_bc.vehicle_no ELSE grn_bc.vehicle_no END AS vehicle_no,
                        CASE WHEN grn_bc.districts_id IS NULL THEN itr_bc.districts_id ELSE grn_bc.districts_id END AS districts_id,
                        CASE WHEN grn_bc.id IS NULL THEN itr_bc.id ELSE grn_bc.id END AS sp_id
                      from mrp_production mrp
                        join stock_picking gip on gip.production_id = mrp.id
                        join stock_lot ss_fac on gip.lot_id = ss_fac.id
                        join stock_picking itr_fac on itr_fac.lot_id = ss_fac.id
                        join stock_picking gdn on gdn.id = itr_fac.backorder_id
                        join stock_lot ss_bc on gdn.lot_id = ss_bc.id
                        join (Select sp.* From stock_picking sp join stock_picking_type spt on sp.picking_type_id = spt.id
                             Where spt.code='incoming') itr_bc on ss_bc.id = itr_bc.lot_id
                        Left join stock_picking grn_bc on grn_bc.id = itr_bc.backorder_id
                      where mrp.state='done')) find_grn
                        LEFT JOIN request_kcs_line rkl ON find_grn.sp_id=rkl.picking_id
                        LEFT JOIN stock_allocation sa ON find_grn.sp_id = sa.picking_id    
                        LEFT JOIN purchase_contract pc ON pc.id = sa.contract_id
                        LEFT JOIN purchase_contract_line pcl ON pc.id = pcl.contract_id
                        LEFT JOIN res_district rdis ON find_grn.districts_id = rdis.id
                        LEFT JOIN market_price mk ON find_grn.date_finished = mk.mdate
                        Order By find_grn.date_finished DESC
                      """)

                        # mrp_sp.batch_no, mrp_sp.date_finished, ss.name stack_name, mrp_sp.day_tz, 
                        # sm.product_uom_qty AS net_quantity, pp.default_code AS product, rkl.deduction, pc.name AS contract, pc.date_order, sa.qty_allocation,
                        # pcl.price_unit AS contract_price, rdis.name AS origin, mk.commercialrate as commrate, sp_sp.*
                        # From (Select sp_bra.id branch_id, sp_bra.name AS grn_bran, sp_fac.name as grn_fact, sp_bra.partner_id, 
                        # Case when sp_bra.picking_type_id IS NULL THEN sp_fac.picking_type_id ELSE sp_bra.picking_type_id END AS picking_type_id, 
                        # case when sp_bra.allocated_qty IS NULL Then sp_fac.allocated_qty Else sp_bra.allocated_qty End As allocated_qty, 
                        # case when sp_bra.qty_available IS NULL Then sp_fac.qty_available Else sp_bra.qty_available End As qty_available, 
                        # case when sp_bra.total_qty IS NULL Then sp_fac.total_qty Else sp_bra.total_qty End As total_qty,
                        # case when sp_bra.total_init_qty IS NULL Then sp_fac.total_init_qty Else sp_bra.total_init_qty End As total_init_qty,
                        # CASE WHEN sp_fac.stack_id IS NULL THEN sp_bra.stack_id ELSE sp_fac.stack_id END AS stack_id, 
                        # CASE WHEN sp_fac.zone_id IS NULL THEN sp_bra.zone_id ELSE sp_fac.zone_id END AS zone_id,
                        # case when sp_bra.total_bag IS NULL Then sp_fac.total_bag Else sp_bra.total_bag End As total_bag,
                        # case when sp_bra.vehicle_no IS NULL Then sp_fac.vehicle_no Else sp_bra.vehicle_no End As vehicle_no,
                        # case when sp_bra.districts_id IS NULL Then sp_fac.districts_id Else sp_bra.districts_id End As districts_id,
                        # case when sp_bra.packing_id IS NULL Then sp_fac.packing_id Else sp_bra.packing_id End As packing_id,
                        # sp_bra.date_done branch_date, sp_fac.date_done factory_date, sp_bra.product_id
                        # From (Select * From stock_picking Where picking_type_code='incoming' and backorder_id is NULL) sp_bra 
                        # Left Join (Select * From stock_picking Where picking_type_code='incoming') sp_fac On sp_bra.id=sp_fac.backorder_id) sp_sp
                        # Left Join
                        # (Select mrp.name Batch_no, sp.stack_id, mrp.date_finished, mrp.day_tz from mrp_production mrp 
                        #  Left Join stock_picking sp On mrp.id = sp.production_id group by mrp.name, sp.stack_id, mrp.date_finished, mrp.day_tz) mrp_sp
                        # On sp_sp.stack_id=mrp_sp.stack_id
                        # LEFT JOIN stock_stack ss ON sp_sp.stack_id = ss.id
                        # LEFT JOIN stock_move sm ON sp_sp.branch_id = sm.picking_id
                        # JOIN stock_picking_type spt ON sp_sp.picking_type_id = spt.id
                        # LEFT JOIN product_product pp ON sm.product_id = pp.id
                        # LEFT JOIN request_kcs_line rkl ON sp_sp.branch_id=rkl.picking_id
                        # LEFT JOIN stock_allocation sa ON sp_sp.branch_id = sa.picking_id    
                        # left JOIN purchase_contract pc ON pc.id = sa.contract_id
                        # left JOIN purchase_contract_line pcl ON pc.id = pcl.contract_id
                        # left JOIN res_district rdis ON sp_sp.districts_id = rdis.id
                        # LEFT JOIN market_price mk ON mrp_sp.date_finished = mk.mdate
