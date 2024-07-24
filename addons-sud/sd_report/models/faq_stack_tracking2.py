# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict
import re
DATE_FORMAT = "%Y-%m-%d"

class faq_stack_tracking(models.Model):
    _name = 'v.faq.stack.tracking'
    _description = 'Storing Loss Analysis'
    _auto = False

    stack_id = fields.Float(string = 'Stack ID')
    name = fields.Char(string = 'Stack Name')
    coffee_type = fields.Char(string = 'Coffee Type')
    product_name = fields.Char(string = 'Product Name')
    date_in = fields.Date(string = 'Date IN')
    qty_in = fields.Float(string = 'Qty IN', digits=(12, 0))
    mc_in = fields.Float(string = 'MC IN', digits=(12, 2))
    date_out = fields.Date(string = 'Date OUT')
    qty_out = fields.Float(string = 'Qty OUT', digits=(12, 0))
    mc_out = fields.Float(string = 'MC OUT', digits=(12, 2))
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')

    st_day = fields.Float(string = 'Storing days', digits=(12, 0))
    loss_kg = fields.Float(string = 'Storing loss (kg)', digits=(12, 0))
    loss_percent = fields.Float(string = 'Storing Loss (%)', digits=(12, 2))
    loss_mc = fields.Float(string = 'MC Loss (%)', digits=(12, 2))
    mc_loss_kg = fields.Float(string = 'MC Loss (kg)', digits=(12, 0))

    unex_loss = fields.Float(string = 'Unexplainable loss (%)', digits=(12, 2))
    unex_loss_kg = fields.Float(string = 'Unexplainable loss (Kg)', digits=(12, 0))

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'v_faq_stack_tracking')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW public.v_faq_stack_tracking AS
              SELECT row_number() OVER () AS id, Case When faq_tracking.product_name = 'FAQ' Then 'FAQ' Else 'Non-FAQ' End As coffee_type, faq_tracking.* FROM
                ((SELECT distinct O.stack_id, ss.name, ss.warehouse_id, pp.default_code product_name, I.date_in, I.qty_in, I.mc_in, O.date_out, O.qty_out, O.mc_out,
                    DATE_PART('day',to_char(O.date_out, 'YYYY-MM-DD')::timestamp - to_char(I.date_in, 'YYYY-MM-DD')::timestamp) st_day,
                    I.qty_in - O.qty_out loss_kg, (I.qty_in - O.qty_out)/I.qty_in * 100 loss_percent, I.mc_in - O.mc_out loss_mc, 
                    Case When I.qty_in = 0 then 0 else round((I.mc_in - O.mc_out) * I.qty_in/100,2) end as mc_loss_kg,
                    Case When I.qty_in = 0 then 0 else round((I.qty_in - O.qty_out) - ((I.mc_in - O.mc_out) * I.qty_in/100),2) end as unex_loss_kg,
                    Case When I.qty_in = 0 or (I.qty_in - O.qty_out)=0 then 0 else round(((I.qty_in - O.qty_out)/I.qty_in * 100) - (I.mc_in - O.mc_out), 2) end as unex_loss --round(((i.qty_in - o.qty_out) - ((i.mc_in - o.mc_out) * i.qty_in/100)) / i.qty_in, 2) 
                FROM (Select sum_prod.stack_id, sum_prod.name, sum_prod.qty_out, 
                    Case When sum_prod.qty_out=0 Then 0 ELSE round(sum_prod.mc_out/sum_prod.qty_out,2) END AS mc_out, sum_prod.date_out
                    FROM (select distinct rkl.stack_id, ss.name, sum(Case When gip.total_init_qty=0 then gip.total_init_qty else gip.total_init_qty end) qty_out, 
                        sum(rkl.mc * (Case When gip.total_init_qty=0 then gip.total_init_qty else gip.total_init_qty end)) mc_out, MAX(gip.date) date_out
                    from stock_picking gip
                    join stock_picking_type gip_type on gip.picking_type_id = gip_type.id
                    join request_kcs_line rkl ON gip.id=rkl.picking_id
                    join stock_lot ss ON gip.lot_id=ss.id
                    Where gip_type.code='production_out' AND gip.state='done' Group by rkl.stack_id, ss.name) sum_prod) O
                JOIN (Select sum_prod.stack_id, sum_prod.name, sum_prod.qty_in, 
                    Case When sum_prod.qty_in=0 Then 0 ELSE round(sum_prod.mc_in/sum_prod.qty_in,2) END AS mc_in, sum_prod.date_in
                    FROM (select distinct rkl.stack_id, ss.name, sum(Case When itr.total_init_qty=0 then itr.total_init_qty else itr.total_init_qty end) qty_in, 
                        sum(rkl.mc * (Case When itr.total_init_qty=0 then itr.total_init_qty else itr.total_init_qty end)) mc_in, MIN(itr.date) date_in
                    from stock_picking itr
                    join stock_picking_type itr_type on itr.picking_type_id = itr_type.id
                    left join stock_picking grn ON itr.backorder_id=grn.id
                    join stock_picking_type grn_type on grn.picking_type_id = grn_type.id
                    join request_kcs_line rkl ON itr.id=rkl.picking_id
                    join stock_lot ss ON itr.lot_id=ss.id
                    Where itr_type.code='incoming' AND itr.state='done' and (itr.backorder_id is null or grn_type.code='incoming')
                        Group by rkl.stack_id, ss.name) sum_prod) I ON O.stack_id=I.stack_id
                JOIN stock_lot ss ON O.stack_id=ss.id
                JOIN product_product pp ON ss.product_id=pp.id) -- Lấy các STACK nhập tại Factory
                UNION ALL
                (SELECT distinct i.lot_id, ss.name, ss.warehouse_id, pp.default_code product_name, i.date_in, i.qty_in, i.mc_in, o.date_out, o.qty_out, o.mc_out,
                    DATE_PART('day',to_char(o.date_out, 'YYYY-MM-DD')::timestamp - to_char(i.date_in, 'YYYY-MM-DD')::timestamp) st_day,
                    i.qty_in - o.qty_out loss_kg, (i.qty_in - o.qty_out)/qty_in * 100 loss_percent, i.mc_in - o.mc_out loss_mc, 
                    Case When i.qty_in = 0 then 0 else round((i.mc_in - o.mc_out) * i.qty_in/100,2) end as mc_loss_kg,
                    Case When i.qty_in = 0 then 0 else round((i.qty_in - o.qty_out) - ((i.mc_in - o.mc_out) * i.qty_in/100),2) end as unex_loss_kg,
                    Case When i.qty_in = 0 or (i.qty_in - o.qty_out)=0 then 0 else round(((i.qty_in - o.qty_out)/qty_in * 100) - (i.mc_in - o.mc_out), 2) end as unex_loss --round(((i.qty_in - o.qty_out) - ((i.mc_in - o.mc_out) * i.qty_in/100)) / i.qty_in, 2) 
                FROM (Select sum_prod.lot_id, sum_prod.date_in, sum_prod.qty_in,
                    Case When sum_prod.qty_in=0 Then 0 ELSE round(sum_prod.mc_in/sum_prod.qty_in,2) END AS mc_in
                    FROM (Select temp.lot_id, MIN(temp.date_in) date_in, sum(temp.qty_in) qty_in, sum(temp.mc_in) mc_in
                        FROM (SELECT distinct itr_bc.lot_id, itr_bc.date date_in, itr_bc.total_init_qty AS qty_in, (rkl.mc * itr_bc.total_init_qty) mc_in
                        From stock_picking itr_bc
                        join stock_picking_type itr_bc_type on itr_bc.picking_type_id = itr_bc_type.id
                        JOIN request_kcs_line rkl ON itr_bc.id = rkl.picking_id
                        join stock_lot ss ON itr_bc.lot_id=ss.id 
                        join stock_picking gdn ON itr_bc.lot_id=gdn.lot_id
                        join stock_picking_type gdn_type on gdn.picking_type_id = gdn_type.id
                        Where itr_bc_type.code='incoming' and ss.name not like '%HP%' and gdn_type.code='transfer_out') temp Group by temp.lot_id) sum_prod) i
                --Out
                JOIN (Select sum_prod.lot_id, sum_prod.date_out, sum_prod.qty_out,
                    Case When sum_prod.qty_out=0 Then 0 ELSE round(sum_prod.mc_out/sum_prod.qty_out,2) END AS mc_out
                    FROM (SELECT grn.lot_id, MAX(gip.date) date_out, sum(Case When grn.total_init_qty = 0 then grn.total_init_qty else grn.total_init_qty end) AS qty_out, 
                        sum(rkl.mc * (Case When grn.total_init_qty = 0 then grn.total_init_qty else grn.total_init_qty end)) mc_out
                    From stock_picking grn
                    join stock_picking_type grn_type on grn.picking_type_id = grn_type.id
                    join stock_picking gip on grn.id = gip.backorder_id
                    JOIN stock_move_line sm ON gip.id = sm.picking_id
                    LEFT JOIN request_kcs_line rkl ON gip.id = rkl.picking_id
                    Where grn_type.code='transfer_out' AND gip.state='done' -- and rkl.product_id=1176 And grn.stack_id=41333
                    Group By grn.lot_id) sum_prod) o ON i.lot_id=o.lot_id
                JOIN stock_lot ss ON i.lot_id=ss.id
                JOIN product_product pp ON ss.product_id=pp.id)
                UNION ALL
                (SELECT distinct O.stack_id, ss.name, ss.warehouse_id, pp.default_code product_name, I.date_in, I.qty_in, I.mc_in, O.date_out, O.qty_out, O.mc_out,
                    DATE_PART('day',to_char(O.date_out, 'YYYY-MM-DD')::timestamp - to_char(I.date_in, 'YYYY-MM-DD')::timestamp) st_day,
                    I.qty_in - O.qty_out loss_kg, (I.qty_in - O.qty_out)/I.qty_in * 100 loss_percent, I.mc_in - O.mc_out loss_mc, 
                    Case When I.qty_in = 0 then 0 else round(((I.mc_in - O.mc_out) * I.qty_in/100)::numeric, 2) end as mc_loss_kg,
                    Case When I.qty_in = 0 then 0 else round(((I.qty_in - O.qty_out) - ((I.mc_in - O.mc_out) * I.qty_in/100))::numeric, 2) end as unex_loss_kg,
                    Case When I.qty_in = 0 or (I.qty_in - O.qty_out)=0 then 0 else round((((I.qty_in - O.qty_out)/I.qty_in * 100) - (I.mc_in - O.mc_out))::numeric, 2) end as unex_loss --round(((i.qty_in - o.qty_out) - ((i.mc_in - o.mc_out) * i.qty_in/100)) / i.qty_in, 2) 
                FROM (Select sum_prod.stack_id, sum_prod.name, sum_prod.qty_out, 
                    Case When sum_prod.qty_out=0 Then 0 ELSE round((sum_prod.mc_out/sum_prod.qty_out)::numeric, 2) END AS mc_out, sum_prod.date_out
                    FROM 
                        ((select distinct rkl.stack_id, ss.name, sum(gip.total_init_qty) qty_out, 
                                sum(rkl.mc * gip.total_init_qty) mc_out, MAX(gip.date) date_out
                            from stock_picking gip
                            join stock_picking_type gip_type on gip.picking_type_id = gip_type.id
                            join request_kcs_line rkl ON gip.id=rkl.picking_id
                            join stock_lot ss ON gip.lot_id=ss.id
                            Where gip_type.code='production_out' AND gip.state='done' Group by rkl.stack_id, ss.name) -- Get GIP ticket
                        UNION ALL
                        (Select distinct gdn.stack_id, gdn.name, gdn.qty_out, (alc.mc_on_despatch * gdn.qty_out) mc_out, gdn.date_out from 
                            (select distinct sm.stack_id, ss.name, sum(sm.init_qty) qty_out, Max(gdn.date) date_out
                            from stock_picking gdn
                            join stock_picking_type gdn_type on gdn.picking_type_id = gdn_type.id
                            join stock_move_line sm ON sm.picking_id=gdn.id
                            join stock_lot ss ON sm.stack_id=ss.id
                            Where gdn_type.code='outgoing' AND gdn.state='done' Group by sm.stack_id, ss.name) gdn
                            join (Select stack_id, sum(mc_on_despatch)/count (*) mc_on_despatch From lot_stack_allocation Group by stack_id) alc ON alc.stack_id=gdn.stack_id)) -- Get GDN ticket
                        sum_prod) O
                JOIN (Select sum_prod.stack_id, sum_prod.name, sum_prod.qty_in, 
                    Case When sum_prod.qty_in=0 Then 0 ELSE round(sum_prod.mc_in/sum_prod.qty_in,2) END AS mc_in, sum_prod.date_in
                    FROM (select distinct rkl.stack_id, ss.name, sum(Case When grp.total_init_qty=0 then grp.total_init_qty else grp.total_init_qty end) qty_in, 
                        sum(rkl.mc * (Case When grp.total_init_qty=0 then grp.total_init_qty else grp.total_init_qty end)) mc_in, MIN(grp.date) date_in
                    from stock_picking grp
                    join stock_picking_type grp_type on grp.picking_type_id = grp_type.id
                    join request_kcs_line rkl ON grp.id=rkl.picking_id
                    join stock_lot ss ON grp.lot_id=ss.id
                    Where grp_type.code='production_in' AND grp.state='done' Group by rkl.stack_id, ss.name) sum_prod) I ON O.stack_id=I.stack_id
                JOIN stock_lot ss ON O.stack_id=ss.id
                JOIN product_product pp ON ss.product_id=pp.id) -- Lấy các STACK nhập Kho từ GRP ra GIP hoặc GDN
                ) faq_tracking 
                JOIN stock_lot ss ON ss.id = faq_tracking.stack_id
                WHERE (faq_tracking.qty_in !=0 or faq_tracking.qty_out !=0)
                -- WHERE faq_tracking.name not like '%HP%' 
                Order By faq_tracking.date_out DESC  
            """)
