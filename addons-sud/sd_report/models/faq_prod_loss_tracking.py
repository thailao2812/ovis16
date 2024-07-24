# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict
import re
DATE_FORMAT = "%Y-%m-%d"


class Input_value(models.Model):
    _name = 'v.faq.prod'
    _description = 'FAQ-Prod. Loss tracking'
    _auto = False

    mrp_name = fields.Char(string = 'Batch No.')
    ss_name = fields.Char(string = 'Stack No.')
    net_quantity = fields.Float(string = 'GIP Qty (Kg)', digits=(12, 0))
    sum_itr_qty = fields.Float(string = 'ITR Qty (Kg)', digits=(12, 0))
    sum_grn_qty = fields.Float(string = 'GRN Qty (Kg)', digits=(12, 0))
    deficit_grn_itr = fields.Float(string = 'Deficit GRN-ITR(Kg)', digits=(12, 0))
    deficit_itr_gip = fields.Float(string = 'Deficit ITR-GIP(Kg)', digits=(12, 0))
    deficit_grn_gip = fields.Float(string = 'GRN Qty (Kg)', digits=(12, 0))

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'v_faq_prod')
        self.env.cr.execute("""
                    CREATE OR REPLACE VIEW public.v_faq_prod AS
                      SELECT row_number() OVER () AS id,
                        A.*, B.*, B.sum_grn_qty-B.sum_itr_qty As deficit_grn_itr, B.sum_itr_qty-A.net_quantity As deficit_itr_gip, 
                            B.sum_grn_qty-A.net_quantity As deficit_grn_gip from 
                         (SELECT mrp.id batch_id, mrp.name AS mrp_name, sp.lot_id sp_id, ss.name AS ss_name, sum(sm.init_qty) AS net_quantity
                          FROM mrp_production mrp
                          JOIN stock_picking sp ON mrp.id = sp.production_id
                          JOIN stock_picking_type spt ON sp.picking_type_id = spt.id
                          LEFT JOIN stock_lot ss ON sp.lot_id = ss.id
                          JOIN stock_move_line sm ON sp.id = sm.picking_id
                          WHERE spt.code::text = 'production_out'::text AND sp.state::text = 'done'::text --and ss.name = 'STACK-17-04785'
                          GROUP BY mrp.id,mrp.name,sp.lot_id,ss.name) A
                        Join (Select sp_sp.stack_id sp_sp_stackid, sum(rkl.product_qty) sum_itr_qty, sum(sm.product_uom_qty) sum_grn_qty From
                          (Select sp_bra.id branch_id, sp_bra.name AS grn_bran, sp_fac.name as grn_fact,
                              CASE WHEN sp_fac.lot_id IS NULL THEN sp_bra.lot_id ELSE sp_fac.lot_id END AS stack_id
                          From (
                              Select sp.* From stock_picking sp join stock_picking_type 
                              spt on sp.picking_type_id = spt.id Where spt.code='incoming' and backorder_id is NULL) sp_bra 
                          Left Join (Select sp.* From stock_picking sp join stock_picking_type spt  on sp.picking_type_id = spt.id 
                           Where spt.code='incoming') sp_fac On sp_bra.id=sp_fac.backorder_id) sp_sp
                          JOIN request_kcs_line rkl ON sp_sp.branch_id=rkl.picking_id
                          join stock_move sm on sp_sp.branch_id = sm.picking_id Group by sp_sp.stack_id) B
                        On A.sp_id=B.sp_sp_stackid Order by A.batch_id desc
                    """)
