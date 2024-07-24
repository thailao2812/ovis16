# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict
import re
DATE_FORMAT = "%Y-%m-%d"

class Output_value(models.Model):
    _name = 'v.output.value'
    _description = 'Output value'
    _auto = False

    batch_no = fields.Char(string = 'Batch No.')
    zone_name = fields.Char(string = 'Zone')
    stack = fields.Char(string = 'Stack')
    start_date = fields.Date(string = 'Start Date')
    stock_note = fields.Char(string = 'Stock Note')
    picking_date = fields.Date(string = 'Date')
    product = fields.Char(string = 'Product')
    net_quantity = fields.Float(string = 'NET Qty', digits=(12, 0))
    mc = fields.Float(string = 'MC', digits=(12, 2))
    fm = fields.Float(string = 'FM', digits=(12, 2))
    black = fields.Float(string = 'Black', digits=(12, 2))
    broken = fields.Float(string = 'Broken', digits=(12, 2))
    brown = fields.Float(string = 'Brown', digits=(12, 2))
    mold = fields.Float(string = 'Mold', digits=(12, 2))
    cherry = fields.Float(string = 'Cherry', digits=(12, 2))
    excelsa = fields.Float(string = 'Excelsa', digits=(12, 2))
    screen20 = fields.Float(string = 'Screen20', digits=(12, 2))
    screen19 = fields.Float(string = 'Screen19', digits=(12, 2))
    screen18 = fields.Float(string = 'Screen18', digits=(12, 2))
    screen16 = fields.Float(string = 'Screen16', digits=(12, 2))
    screen13 = fields.Float(string = 'Screen13', digits=(12, 2))
    eaten = fields.Float(string = 'Insect', digits=(12, 2))
    burn = fields.Float(string = 'Burn', digits=(12, 2))
    immature = fields.Float(string = 'Immature', digits=(12, 2))
    screen12 = fields.Float(string = 'Screen12', digits=(12, 2))
    premium = fields.Float(string = 'Premium/Disct', digits=(12, 2))

    def init(self):
        
        tools.drop_view_if_exists(self.env.cr, 'v_output_value')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW public.v_output_value AS
            SELECT row_number() OVER (ORDER BY (mrp.name ,bom.code, sz.name, mrp.date_planned_start , sp.name , sp.date_done::date, ss.name , pp.default_code , sm.state) DESC) AS id,
                mrp.name AS batch_no,
                bom.code AS bom_type,
                sz.name As zone_name,
                mrp.date_planned_start AS start_date,
                sp.name AS stock_note,
                sp.date_done::date AS picking_date,
                ss.name AS stack,
                pp.default_code AS product,
                    CASE
                        WHEN spt.code::text = 'production_out'::text THEN 1
                        ELSE '-1'::integer
                    END::numeric * sm.qty_done AS net_quantity,
                ss.mc,
                ss.fm,
                ss.black,
                ss.broken,
                ss.brown,
                ss.mold,
                ss.cherry,
                ss.excelsa,
                ss.screen20,
                ss.screen19,
                ss.screen18,
                ss.screen16,
                ss.screen13,
                ss.eaten,
                ss.burn,
                ss.immature,
                ss.screen12,
                sm.state,
                sp.note AS remarks,
                mpl.premium
               FROM mrp_production mrp
                 JOIN stock_picking sp ON mrp.id = sp.production_id
                 JOIN stock_zone sz ON sp.zone_id = sz.id
                 JOIN stock_picking_type spt ON sp.picking_type_id = spt.id
                 JOIN mrp_bom_premium_line mpl ON sp.product_id = mpl.product_id
                 LEFT JOIN stock_lot ss ON sp.lot_id = ss.id
                 JOIN stock_move_line sm ON sp.id = sm.picking_id
                 JOIN product_product pp ON sm.product_id = pp.id
                 JOIN mrp_bom bom ON mrp.bom_id = bom.id
              WHERE spt.code::text = 'production_in'::text and mrp.state::text = 'done'::text
              ORDER BY 
                mrp.name ,
                bom.code,
                sz.name,
                mrp.date_planned_start ,
                sp.name ,
                sp.date_done::date,
                ss.name ,
                pp.default_code ,
                sm.state;
                
                
          """)