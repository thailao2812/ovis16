# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from bisect import bisect_left
from collections import defaultdict
import re
from time import gmtime, strftime
DATE_FORMAT = "%Y-%m-%d"

class Internal_Transfer_Tracking(models.Model):
    _name = 'v.itn.tracking'
    _description = 'Internal Transfer Notes Tracking'
    _auto = False

    name = fields.Char(string = 'TO No.')
    truck_com = fields.Char(string = 'Trucking Co.')
    vehicle_no = fields.Char(string = 'Vehicle No.')
    product = fields.Char(string = 'Product')
    packing_name = fields.Char(string = 'Packing')
    bag_issue = fields.Float(string = 'Bags', digits=(12, 0), group_operator="avg")
    from_wh = fields.Char(string = 'From WH')
    to_wh = fields.Char(string = 'To WH')

    gti_name = fields.Char(string = 'GTI Name')
    gtr_name = fields.Char(string = 'GTR Name')
    date_issue = fields.Datetime(string = 'Issue Date')
    date_receipt = fields.Datetime(string = 'Receipt Date')
    gti_stack = fields.Char(string = 'Issue Stack')
    gtr_stack = fields.Char(string = 'Receipt Stack')

    qty_issue = fields.Float(string = 'Issue Qty. (kg)', digits=(12, 0), group_operator="avg")
    qty_receipt = fields.Float(string = 'Receipt Qty. (kg)', digits=(12, 0), group_operator="avg")
    diff_qty = fields.Float(string = 'Qty +/- (kg)', digits=(12, 0), group_operator="avg")
    qty_per = fields.Float(string = 'Qty +/- (%)', digits=(12, 2), group_operator="avg")
    deficit = fields.Char(string = 'Deficit')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'v_itn_tracking')
        self.env.cr.execute(""" 
        CREATE OR REPLACE VIEW v_itn_tracking AS 
            Select row_number() OVER (ORDER BY b.id desc) AS id, 
                b.origin AS name,
                b.truck_com,
                b.vehicle_no,
                b.product,
                b.packing_name,
                b.wh_name AS from_wh,
                f.wh_name AS to_wh,
                b.name AS gti_name,
                b.date_done AS date_issue,
                b.stack_name AS gti_stack,
                f.name AS gtr_name,
                f.date_done AS date_receipt,
                f.stack_name AS gtr_stack,
                b.bag_no AS bag_issue,
                f.bag_no AS bag_receipt,
                b.bag_no - f.bag_no AS diff_bag,
                b.init_qty AS qty_issue,
                f.init_qty AS qty_receipt,
                f.init_qty - b.init_qty AS diff_qty,
                (f.init_qty - b.init_qty) /
                CASE
                    WHEN b.init_qty > f.init_qty THEN b.init_qty
                    ELSE f.init_qty
                END * 100::numeric AS qty_per,
                CASE
                    WHEN (b.init_qty - f.init_qty) > 0 THEN 'Deficit'::text
                    ELSE ''::text
                END AS deficit
                FROM ( SELECT sp_b.id, sp_b.origin, sp_b.name, sp_b.date_done, rpn_truck.shortname truck_com, pp.default_code AS product, 
                            sp_b.vehicle_no, sw.name wh_name, ss.name stack_name, np.name packing_name, sm.bag_no,
                            case when (sm.weighbridge = 0 or sm.weighbridge is null) then sm.init_qty else sm.weighbridge End As init_qty
                        FROM stock_picking sp_b
                        join stock_picking_type spt on sp_b.picking_type_id = spt.id
                        LEFT JOIN res_partner rpn_truck ON sp_b.trucking_id = rpn_truck.id
                        JOIN stock_move_line sm ON sp_b.id = sm.picking_id
                        JOIN stock_lot ss ON ss.id = sm.lot_id
                        JOIN ned_packing np ON np.id = sm.packing_id
                        JOIN product_product pp ON sm.product_id = pp.id
                        JOIN stock_warehouse sw ON sw.id=sp_b.warehouse_id
                        WHERE spt.code = 'transfer_out' AND sp_b.backorder_id IS NULL) b
                LEFT JOIN ( SELECT sp_f.backorder_id, sp_f.name, sp_f.date_done, sw.name wh_name, ss.name stack_name, 
                                sm.bag_no, case when (sm.weighbridge = 0 or sm.weighbridge is null) then sm.init_qty else sm.weighbridge End As init_qty
                        FROM stock_picking sp_f
                        join stock_picking_type sp_f_type on sp_f.picking_type_id = sp_f_type.id
                        JOIN stock_move_line sm ON sp_f.id = sm.picking_id
                        JOIN stock_lot ss ON ss.id = sm.lot_id
                        JOIN stock_warehouse sw ON sw.id=sp_f.warehouse_id
                        WHERE sp_f_type.code::text = 'transfer_in'::text) f ON b.id = f.backorder_id;
            """)








