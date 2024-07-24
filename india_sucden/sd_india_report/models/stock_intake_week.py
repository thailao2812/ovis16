# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict
DATE_FORMAT = "%Y-%m-%d"

class StockIntakeQtyWeek(models.Model):
    _name = 'v.intake.qty.week'
    _description = 'Stock Intake Qty Week'
    _auto =False

    week_name = fields.Char(string = 'Week')
    w_num = fields.Char(string = 'w_num')
    y_num = fields.Char(string = 'Year')
    product = fields.Char(string = 'Product')
    source_province = fields.Char(string= 'Province')
    net_qty = fields.Float(string = 'Net Qty.', digits=(12, 0))

    mc = fields.Float(string = 'MC', group_operator = 'avg', digits=(12, 2))
    fm = fields.Float(string = 'FM', group_operator = 'avg', digits=(12, 2))
    black = fields.Float(string = 'Bl.', group_operator = 'avg', digits=(12, 2))
    broken = fields.Float(string = 'Brk.', group_operator = 'avg', digits=(12, 2))
    brown = fields.Float(string = 'Brw.', group_operator = 'avg', digits=(12, 2))
    mold = fields.Float(string = 'Mol.', group_operator = 'avg', digits=(12, 2))
    cherry = fields.Float(string = 'Chr.', group_operator = 'avg', digits=(12, 2))
    excelsa = fields.Float(string = 'Ex.', group_operator = 'avg', digits=(12, 2))
    screen20 = fields.Float(string = 'Scr20', group_operator = 'avg', digits=(12, 2))
    screen19 = fields.Float(string = 'Scr19', group_operator = 'avg', digits=(12, 2))
    screen18 = fields.Float(string = 'Scr18', group_operator = 'avg', digits=(12, 2))
    screen16 = fields.Float(string = 'Scr16', group_operator = 'avg', digits=(12, 2))
    screen13 = fields.Float(string = 'Scr13', group_operator = 'avg', digits=(12, 2))
    screen12 = fields.Float(string = 'Scr12', group_operator = 'avg', digits=(12, 2))
    belowsc12 = fields.Float(string = 'Bl-12', group_operator = 'avg', digits=(12, 2))
    burned = fields.Float(string = 'Burned', group_operator = 'avg', digits=(12, 2))
    eaten = fields.Float(string = 'Insect', group_operator = 'avg', digits=(12, 2))
    immature = fields.Float(string = 'Imt.', group_operator = 'avg', digits=(12, 2))
    # product = fields.Char(string='Product')
    # receipt_qty = fields.Float(string="Receipt Qty.", digits=(12, 2))
    # supplier = fields.Char(string = 'Supplier')
    # supplier_id = fields.Char(string="Suppler Id")
    # source_dis = fields.Char(string = 'District')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'v_intake_qty_week')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW public.v_intake_qty_week AS
            SELECT row_number() OVER () AS id,
                concat('Week ',(SELECT EXTRACT(week FROM sp.date_done::TIMESTAMP))) week_name,
                (SELECT EXTRACT(week FROM sp.date_done::TIMESTAMP)) w_num,
                concat('',(SELECT EXTRACT(year FROM sp.date_done::TIMESTAMP))) y_num,
                pp.default_code AS product, 
                rcs.name as source_province, 
                sum(rkl.product_qty) AS net_qty,
                sum(rkl.mc * rkl.product_qty)/sum(rkl.product_qty) mc,
                sum(rkl.fm * rkl.product_qty)/sum(rkl.product_qty) fm,
                sum(rkl.black * rkl.product_qty)/sum(rkl.product_qty) black,
                sum(rkl.broken * rkl.product_qty)/sum(rkl.product_qty) broken,
                sum(rkl.brown * rkl.product_qty)/sum(rkl.product_qty) brown,
                sum(rkl.mold * rkl.product_qty)/sum(rkl.product_qty) mold,
                sum(rkl.cherry * rkl.product_qty)/sum(rkl.product_qty) cherry,
                sum(rkl.excelsa * rkl.product_qty)/sum(rkl.product_qty) excelsa,
                sum(rkl.screen20 * rkl.product_qty)/sum(rkl.product_qty) screen20,
                sum(rkl.screen19 * rkl.product_qty)/sum(rkl.product_qty) screen19,
                sum(rkl.screen18 * rkl.product_qty)/sum(rkl.product_qty) screen18,
                sum(rkl.screen16 * rkl.product_qty)/sum(rkl.product_qty) screen16,
                sum(rkl.screen13 * rkl.product_qty)/sum(rkl.product_qty) screen13,
                sum(rkl.greatersc12 * rkl.product_qty)/sum(rkl.product_qty) screen12,
                sum(rkl.belowsc12 * rkl.product_qty)/sum(rkl.product_qty) belowsc12,
                sum(rkl.burned * rkl.product_qty)/sum(rkl.product_qty) burned,
                sum(rkl.eaten * rkl.product_qty)/sum(rkl.product_qty) eaten,
                sum(rkl.immature * rkl.product_qty)/sum(rkl.product_qty) immature
            FROM stock_lot sc
                JOIN stock_picking sp ON sc.id = sp.lot_id
                JOIN stock_picking_type spt on sp.picking_type_id = spt.id
                LEFT JOIN stock_move_line sm ON sp.id = sm.picking_id
                JOIN request_kcs_line rkl ON sp.id = rkl.picking_id
                JOIN product_product pp ON sm.product_id = pp.id
                LEFT  JOIN res_district rd ON sc.districts_id=rd.id
                JOIN res_country_state rcs ON rd.state_id = rcs.id
            Where spt.code in ('incoming','transfer_in') and rkl.product_qty != 0
            Group by (SELECT EXTRACT(week FROM sp.date_done::TIMESTAMP)),
            (SELECT EXTRACT(year FROM sp.date_done::TIMESTAMP)),
            pp.default_code, rcs.name 
            Order by (SELECT EXTRACT(year FROM sp.date_done::TIMESTAMP)) desc, (SELECT EXTRACT(week FROM  sp.date_done::TIMESTAMP)) desc
            """)