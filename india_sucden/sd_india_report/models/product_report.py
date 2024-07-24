# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from bisect import bisect_left
from collections import defaultdict
import re
from time import gmtime, strftime
DATE_FORMAT = "%Y-%m-%d"

class ProductionReport(models.Model):
    _name = 'v.production.report'
    _auto = False
    _description = 'Production Report'
    
    batch_no = fields.Char(string = 'Batch no.')
    bom_type = fields.Char(string = 'BOM')
    start_date = fields.Date(string = 'Start')
    stock_note = fields.Char(string = 'Picking')

    operation_type = fields.Char(string = 'Type')
    picking_date = fields.Date(string = 'Picking date')
    stack = fields.Char(string = 'Stack')
    product = fields.Char(string = 'Product')

    weighbridge = fields.Float(string = 'Net weight.', digits=(12, 0))
    net_quantity = fields.Float(string = 'Net weight', digits=(12, 0))

    mc = fields.Float(string = 'MC', digits=(12, 2), group_operator="avg")
    fm = fields.Float(string = 'FM', digits=(12, 2), group_operator="avg")
    black = fields.Float(string = 'Black', digits=(12, 2), group_operator="avg")
    broken = fields.Float(string = 'Broken', digits=(12, 2), group_operator="avg")
    brown = fields.Float(string = 'Brown', digits=(12, 2), group_operator="avg")
    mold = fields.Float(string = 'Moldy', digits=(12, 2), group_operator="avg")
    cherry = fields.Float(string = 'Cherry', digits=(12, 2), group_operator="avg")
    excelsa = fields.Float(string = 'Excelsa', digits=(12, 2), group_operator="avg")
    screen20 = fields.Float(string = 'Scr20', digits=(12, 2), group_operator="avg")
    screen19 = fields.Float(string = 'Scr19', digits=(12, 2), group_operator="avg")
    screen18 = fields.Float(string = 'Scr18', digits=(12, 2), group_operator="avg")
    screen16 = fields.Float(string = 'Scr16', digits=(12, 2), group_operator="avg")
    screen13 = fields.Float(string = 'Scr13', digits=(12, 2), group_operator="avg")
    greatersc12 = fields.Float(string = 'Scr12', digits=(12, 2), group_operator="avg")
    belowsc12 = fields.Float(string = 'BlwSC12', digits=(12, 2), group_operator="avg")
    eaten = fields.Float(string = 'Insect', digits=(12, 2), group_operator="avg")
    burn = fields.Float(string = 'Burned', digits=(12, 2), group_operator="avg")
    immature = fields.Float(string = 'Immature', digits=(12, 2), group_operator="avg")
    state = fields.Char(string = 'State')
    remarks = fields.Char(string = 'Remarks')
    zone = fields.Char(string='Zone')
    bag_no = fields.Float(string='Bags', digits=(12, 0), group_operator="sum")
    packing = fields.Char(string='Packing Type')
    date_end = fields.Date(string='End Date')

    outturn_percent = fields.Float(string='Outturn%', compute='compute_qc_india', store=True, digits=(12, 2))
    aaa_percent = fields.Float(string="AAA%", compute='compute_qc_india', store=True)
    aa_percent = fields.Float(string="AA%", compute='compute_qc_india', store=True)
    a_percent = fields.Float(string="A%", compute='compute_qc_india', store=True)
    b_percent = fields.Float(string="B%", compute='compute_qc_india', store=True)
    c_percent = fields.Float(string="C%", compute='compute_qc_india', store=True)
    pb_percent = fields.Float(string="PB%", compute='compute_qc_india', store=True)
    bb_percent = fields.Float(string="BB%", compute='compute_qc_india', store=True)
    bleached_percent = fields.Float(string="Bleached%", compute='compute_qc_india', store=True)
    idb_percent = fields.Float(string="IDB%", compute='compute_qc_india', store=True)
    bits_percent = fields.Float(string="Bits%", compute='compute_qc_india', store=True)
    hulks_percent = fields.Float(string="Husk%", compute='compute_qc_india', store=True)
    stone_percent = fields.Float(string="Stone%", compute='compute_qc_india', store=True)
    skin_out_percent = fields.Float(string='Skin Out%', compute='compute_qc_india', store=True)
    triage_percent = fields.Float(string='Triage%', compute='compute_qc_india', store=True)
    wet_bean_percent = fields.Float(string='Wet Beans%', compute='compute_qc_india', store=True)
    red_beans_percent = fields.Float(string='Red Beans%', compute='compute_qc_india', store=True)
    stinker_percent = fields.Float(string='Stinker%', compute='compute_qc_india', store=True)
    faded_percent = fields.Float(string='Faded%', compute='compute_qc_india', store=True)
    flat_percent = fields.Float(string='Flat%', compute='compute_qc_india', store=True)
    pb1_percent = fields.Float(string='PB1%', compute='compute_qc_india', store=True)
    pb2_percent = fields.Float(string='PB2%', compute='compute_qc_india', store=True)
    sleeve_6_up_percent = fields.Float(string='6↑ %', compute='compute_qc_india', store=True)
    sleeve_5_5_up_percent = fields.Float(string='5.5↑ %', compute='compute_qc_india', store=True)
    sleeve_5_5_down_percent = fields.Float(string='5.5↓%', compute='compute_qc_india', store=True)
    sleeve_5_down_percent = fields.Float(string='5↓ %', compute='compute_qc_india', store=True)

    sleeve_5_up_percent = fields.Float(string='5↑ %', digits=(12, 2), compute='compute_qc_india', store=True)
    unhulled_percent = fields.Float(string='Unhulled %', digits=(12, 2), compute='compute_qc_india', store=True)
    remaining_coffee_percent = fields.Float(string='Remaining Coffee %', digits=(12, 2), compute='compute_qc_india',store=True)
    blacks_percent = fields.Float(string='Blacks %', digits=(12, 2), compute='compute_qc_india', store=True)
    half_monsoon_percent = fields.Float(string='Half Monsoon %', digits=(12, 2), compute='compute_qc_india', store=True)
    good_beans_percent = fields.Float(string='Good Beans %', digits=(12, 2), compute='compute_qc_india', store=True)

    moisture_percent = fields.Float(string='Moisture%', digits=(12, 2), compute='compute_qc_india', store=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'v_production_report')
        self.env.cr.execute('''
                   CREATE OR REPLACE VIEW public.v_production_report AS
                        SELECT row_number() OVER (
                            ORDER BY (mrp.date_finished, mrp.name ,bom.code, mrp.date_planned_start , sp.name , sp.date_done::date, ss.name , pp.default_code ) DESC
                        
                        ) AS id,
                        mrp.name AS batch_no,
                        mrp.date_finished AS date_end,
                        bom.code AS bom_type,
                        mrp.date_planned_start AS start_date,
                        sp.name AS stock_note,
                            CASE
                                WHEN spt.code::text = 'production_out'::text THEN 'IN'::text
                                ELSE 'OUT'::text
                            END AS operation_type,
                        sp.date_done::date AS picking_date,
                        ss.name AS stack,
                        pp.display_wb as product,
                        sm.init_qty AS net_quantity,
                            CASE
                                WHEN spt.code::text = 'production_in'::text THEN sm.weighbridge::double precision
                                WHEN spt.code::text = 'production_out'::text THEN sm.weighbridge
                                ELSE NULL::double precision
                            END AS weighbridge,
                        rkl.mc,
                        rkl.fm,
                        rkl.black,
                        rkl.broken,
                        rkl.brown,
                        rkl.mold,
                        rkl.cherry,
                        rkl.excelsa,
                        rkl.screen20,
                        rkl.screen19,
                        rkl.screen18,
                        rkl.screen16,
                        rkl.screen13,
                        rkl.greatersc12,
                        rkl.belowsc12,
                        rkl.eaten,
                        rkl.burned AS burn,
                        rkl.immature,
                        sm.state,
                        sp.note AS remarks,
                        rkl.stick_count,
                        rkl.stone_count,
                        rkl.outturn_percent,
                        rkl.aaa_percent,
                        rkl.aa_percent,
                        rkl.a_percent,
                        rkl.b_percent,
                        rkl.c_percent,
                        rkl.pb_percent,
                        rkl.bb_percent,
                        rkl.bleached_percent,
                        rkl.idb_percent,
                        rkl.bits_percent,
                        rkl.hulks_percent,
                        rkl.stone_percent,
                        rkl.skin_out_percent,
                        rkl.triage_percent,
                        rkl.wet_bean_percent,
                        rkl.red_beans_percent,
                        rkl.stinker_percent,
                        rkl.faded_percent,
                        rkl.flat_percent,
                        rkl.pb1_percent,
                        rkl.pb2_percent,
                        rkl.sleeve_6_up_percent,
                        rkl.sleeve_5_5_up_percent,
                        rkl.sleeve_5_5_down_percent,
                        rkl.sleeve_5_down_percent,
                        
                        rkl.sleeve_5_up_percent,
                        rkl.unhulled_percent,
                        rkl.remaining_coffee_percent,
                        rkl.blacks_percent,
                        rkl.half_monsoon_percent,
                        rkl.good_beans_percent,
                        
                        rkl.moisture_percent,
                        zone.name AS zone,
                        sm.bag_no,
                        np.name AS packing,
                        ctg.name AS prod_group
                       FROM mrp_production mrp
                         JOIN stock_picking sp ON mrp.id = sp.production_id
                         JOIN stock_picking_type spt ON sp.picking_type_id = spt.id
                         LEFT JOIN stock_lot ss ON sp.lot_id = ss.id
                         JOIN stock_move_line sm ON sp.id = sm.picking_id
                         JOIN product_product pp ON sm.product_id = pp.id
                         JOIN mrp_bom bom ON mrp.bom_id = bom.id
                         LEFT JOIN request_kcs_line rkl ON sp.id = rkl.picking_id
                         LEFT JOIN ned_packing np ON sm.packing_id = np.id
                         LEFT JOIN stock_zone zone ON ss.zone_id = zone.id
                         JOIN product_template pt ON pt.id = pp.product_tmpl_id
                         JOIN product_category ctg ON ctg.id = pt.categ_id
                      WHERE (spt.code::text = ANY (ARRAY['production_out'::text, 'production_in'::text])) AND sp.state::text <> 'cancel'::text
                      ORDER BY mrp.name,
                            CASE
                                WHEN spt.code::text = 'production_out'::text THEN 'IN'::text
                                ELSE 'OUT'::text
                            END;
        ''')