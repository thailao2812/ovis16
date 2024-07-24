# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from datetime import datetime, date, timedelta

DATE_FORMAT = "%Y-%m-%d"
import calendar


class LongShortFOB(models.Model):
    _name = 'v.long.short.v2'
    _description = 'Long/Short FOB'
    _auto = False

    def add_months(sourcedate, months):
        month = sourcedate.month - 1 + months
        year = int(sourcedate.year + month / 12)
        month = month % 12 + 1
        day = min(sourcedate.day, calendar.monthrange(year, month)[1])
        return date(year, month, day)

    def get_month_year(sdate):
        to_date = sdate.strftime('%b %y')
        return to_date

    a = datetime.now()

    prod_group = fields.Char(string='Prod. Group')
    product = fields.Char(string='Product Code')
    product_id = fields.Many2one('product.product', string='Prod. ID')
    sitting_stock = fields.Float(string='Current Stock', digits=(12, 0))

    npe_received_unfixed = fields.Float(string='NPE Unfixed', digits=(12, 0))
    gross_ls = fields.Float(string='  Gross Long/Short', digits=(12, 0))
    nvp_receivable = fields.Float(string='To be Received', digits=(12, 0))
    unshipped_qty = fields.Float(string='To be Shipped', digits=(12, 0))
    net_ls = fields.Float(string=get_month_year(add_months(a, 0)) + ' L/S', digits=(12, 0))

    nvp_next1_receivable = fields.Float(string=get_month_year(add_months(a, 1)) + ' - TB Receivable', digits=(12, 0))
    sale_next1_unshipped = fields.Float(string=get_month_year(add_months(a, 1)) + ' - TB Shipped', digits=(12, 0))
    next1_net_ls = fields.Float(string=get_month_year(add_months(a, 1)) + ' L/S', digits=(12, 0))

    nvp_next2_receivable = fields.Float(string=get_month_year(add_months(a, 2)) + ' - TB Receivable', digits=(12, 0))
    sale_next2_unshipped = fields.Float(string=get_month_year(add_months(a, 2)) + ' - TB Shipped', digits=(12, 0))
    next2_net_ls = fields.Float(string=get_month_year(add_months(a, 2)) + ' L/S', digits=(12, 0))

    nvp_next3_receivable = fields.Float(string=get_month_year(add_months(a, 3)) + ' - TB Receivable', digits=(12, 0))
    sale_next3_unshipped = fields.Float(string=get_month_year(add_months(a, 3)) + ' - TB Shipped', digits=(12, 0))
    next3_net_ls = fields.Float(string=get_month_year(add_months(a, 3)) + ' L/S', digits=(12, 0))

    nvp_next4_receivable = fields.Float(string=get_month_year(add_months(a, 4)) + ' - TB Receivable', digits=(12, 0))
    sale_next4_unshipped = fields.Float(string=get_month_year(add_months(a, 4)) + ' - TB Shipped', digits=(12, 0))
    next4_net_ls = fields.Float(string=get_month_year(add_months(a, 4)) + ' L/S', digits=(12, 0))

    nvp_next5_receivable = fields.Float(string=get_month_year(add_months(a, 5)) + ' - TB Receivable', digits=(12, 0))
    sale_next5_unshipped = fields.Float(string=get_month_year(add_months(a, 5)) + ' - TB Shipped', digits=(12, 0))
    next5_net_ls = fields.Float(string=get_month_year(add_months(a, 5)) + ' L/S', digits=(12, 0))

    nvp_next6_receivable = fields.Float(string=get_month_year(add_months(a, 6)) + ' - TB Receivable', digits=(12, 0))
    sale_next6_unshipped = fields.Float(string=get_month_year(add_months(a, 6)) + ' - TB Shipped', digits=(12, 0))
    next6_net_ls = fields.Float(string=get_month_year(add_months(a, 6)) + ' L/S', digits=(12, 0))
    faq_derivable = fields.Float(string='FAQ Derivable', digits=(12, 0))

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'v_long_short_v2')
        self.env.cr.execute("""
        CREATE OR REPLACE VIEW public.v_long_short_v2 AS 
 SELECT row_number() OVER (ORDER BY (ROW(longshort.prod_group, longshort.product)) DESC) AS id,
    longshort.prod_group,
    longshort.product,
    longshort.product_id,
    longshort.sitting_stock,
    longshort.npe_received_unfixed,
    longshort.gross_ls,
    longshort.nvp_receivable,
    longshort.unshipped_qty,
    longshort.net_ls,
    longshort.nvp_next1_receivable,
    longshort.sale_next1_unshipped,
    longshort.next1_net_ls,
    longshort.nvp_next2_receivable,
    longshort.sale_next2_unshipped,
    longshort.next2_net_ls,
    longshort.nvp_next3_receivable,
    longshort.sale_next3_unshipped,
    longshort.next3_net_ls,
    longshort.nvp_next4_receivable,
    longshort.sale_next4_unshipped,
    longshort.next4_net_ls,
    longshort.nvp_next5_receivable,
    longshort.sale_next5_unshipped,
    longshort.next5_net_ls,
    longshort.nvp_next6_receivable,
    longshort.sale_next6_unshipped,
    longshort.next6_net_ls,
    longshort.faq_derivable
   FROM ( SELECT row_number() OVER () AS id,
            ctg.name AS prod_group,
            ppp.default_code AS product,
            ppp.id AS product_id,
                CASE
                    WHEN stk.bag_qty = 0::numeric THEN 0::double precision
                    ELSE sum(stk.init_qty)::double precision
                END AS sitting_stock,
            0 AS npe_received_unfixed,
            0 AS gross_ls,
                CASE
                    WHEN (sct.no_of_pack - (( SELECT sum(stm.bag_no) AS sum
                       FROM stock_move_line stm
                         JOIN product_product pp ON pp.id = stm.product_id
                         JOIN product_template ptp_1 ON ptp_1.id = pp.product_tmpl_id
                         JOIN product_category pc ON pc.id = ptp_1.categ_id
                         JOIN stock_lot ss ON ss.id = stm.lot_id
                         JOIN stock_picking sp ON sp.id = stm.picking_id AND sp.state::text = 'done'::text
                         JOIN stock_warehouse sw ON sw.id = sp.warehouse_id
                         JOIN stock_move_line trm ON trm.picking_id = sp.id
                         JOIN s_contract pcon ON pcon.id = sp.pcontract_id
                         JOIN ned_certificate cert ON cert.id = pcon.certificate_id
                         JOIN s_period spe ON spe.id = pcon.shipt_month
                      WHERE ss.id = stk.id))::double precision) = 0::double precision OR (sct.p_qty - (( SELECT sum(stm.init_qty) AS sum
                       FROM stock_move_line stm
                         JOIN product_product pp ON pp.id = stm.product_id
                         JOIN product_template ptp_1 ON ptp_1.id = pp.product_tmpl_id
                         JOIN product_category pc ON pc.id = ptp_1.categ_id
                         JOIN stock_lot ss ON ss.id = stm.lot_id
                         JOIN stock_picking sp ON sp.id = stm.picking_id AND sp.state::text = 'done'::text
						 
                      WHERE ss.id = stk.id))::double precision) < 0::double precision THEN 0::double precision
                    ELSE sct.p_qty - (( SELECT sum(stm.init_qty) AS sum
                       FROM stock_move_line stm
                         JOIN product_product pp ON pp.id = stm.product_id
                         JOIN product_template ptp_1 ON ptp_1.id = pp.product_tmpl_id
                         JOIN product_category pc ON pc.id = ptp_1.categ_id
                         JOIN stock_lot ss ON ss.id = stm.lot_id
                         JOIN stock_picking sp ON sp.id = stm.picking_id AND sp.state::text = 'done'::text
						 JOIN stock_warehouse sw ON sw.id = stm.warehouse_id 
                      WHERE ss.id = stk.id and sw.x_is_bonded = TRUE))::double precision
                END AS nvp_receivable,
            0::double precision AS unshipped_qty,
                CASE
                    WHEN stk.bag_qty = 0::numeric THEN 0::double precision
                    ELSE sum(stk.init_qty)::double precision +
                    CASE
                        WHEN (sct.no_of_pack - (( SELECT sum(stm.bag_no) AS sum
                           FROM stock_move_line stm
                             JOIN product_product pp ON pp.id = stm.product_id
                             JOIN product_template ptp_1 ON ptp_1.id = pp.product_tmpl_id
                             JOIN product_category pc ON pc.id = ptp_1.categ_id
                             JOIN stock_lot ss ON ss.id = stm.lot_id
                             JOIN stock_picking sp ON sp.id = stm.picking_id AND sp.state::text = 'done'::text
                             JOIN stock_warehouse sw ON sw.id = sp.warehouse_id
                             JOIN stock_move_line trm ON trm.picking_id = sp.id
                             JOIN s_contract pcon ON pcon.id = sp.pcontract_id
                             JOIN ned_certificate cert ON cert.id = pcon.certificate_id
                             JOIN s_period spe ON spe.id = pcon.shipt_month
                          WHERE ss.id = stk.id))::double precision) = 0::double precision OR (sct.p_qty - (( SELECT sum(stm.init_qty) AS sum
                           FROM stock_move_line stm
                             JOIN product_product pp ON pp.id = stm.product_id
                             JOIN product_template ptp_1 ON ptp_1.id = pp.product_tmpl_id
                             JOIN product_category pc ON pc.id = ptp_1.categ_id
                             JOIN stock_lot ss ON ss.id = stm.lot_id
                             JOIN stock_picking sp ON sp.id = stm.picking_id AND sp.state::text = 'done'::text
                          WHERE ss.id = stk.id))::double precision) < 0::double precision THEN 0::double precision
                        ELSE sct.p_qty - (( SELECT sum(stm.init_qty) AS sum
                           FROM stock_move_line stm
                             JOIN product_product pp ON pp.id = stm.product_id
                             JOIN product_template ptp_1 ON ptp_1.id = pp.product_tmpl_id
                             JOIN product_category pc ON pc.id = ptp_1.categ_id
                             JOIN stock_lot ss ON ss.id = stm.lot_id
                             JOIN stock_picking sp ON sp.id = stm.picking_id AND sp.state::text = 'done'::text
                          JOIN stock_warehouse sw ON sw.id = stm.warehouse_id 
                      WHERE ss.id = stk.id and sw.x_is_bonded = TRUE))::double precision
                    END
                END 
				AS net_ls,
            0 AS nvp_next1_receivable,
            0 AS sale_next1_unshipped,
                CASE
                    WHEN stk.bag_qty = 0::numeric THEN 0::double precision
                    ELSE sum(stk.init_qty)::integer::double precision +
                    CASE
                        WHEN (sct.no_of_pack - (( SELECT sum(stm.bag_no) AS sum
                           FROM stock_move_line stm
                             JOIN product_product pp ON pp.id = stm.product_id
                             JOIN product_template ptp_1 ON ptp_1.id = pp.product_tmpl_id
                             JOIN product_category pc ON pc.id = ptp_1.categ_id
                             JOIN stock_lot ss ON ss.id = stm.lot_id
                             JOIN stock_picking sp ON sp.id = stm.picking_id AND sp.state::text = 'done'::text
                             JOIN stock_warehouse sw ON sw.id = sp.warehouse_id
                             JOIN stock_move_line trm ON trm.picking_id = sp.id
                             JOIN s_contract pcon ON pcon.id = sp.pcontract_id
                             JOIN ned_certificate cert ON cert.id = pcon.certificate_id
                             JOIN s_period spe ON spe.id = pcon.shipt_month
                          WHERE ss.id = stk.id))::double precision) = 0::double precision OR (sct.p_qty - (( SELECT sum(stm.init_qty) AS sum
                           FROM stock_move_line stm
                             JOIN product_product pp ON pp.id = stm.product_id
                             JOIN product_template ptp_1 ON ptp_1.id = pp.product_tmpl_id
                             JOIN product_category pc ON pc.id = ptp_1.categ_id
                             JOIN stock_lot ss ON ss.id = stm.lot_id
                             JOIN stock_picking sp ON sp.id = stm.picking_id AND sp.state::text = 'done'::text
                          WHERE ss.id = stk.id))::double precision) < 0::double precision THEN 0::double precision
                        ELSE sct.p_qty - (( SELECT sum(stm.init_qty) AS sum
                           FROM stock_move_line stm
                             JOIN product_product pp ON pp.id = stm.product_id
                             JOIN product_template ptp_1 ON ptp_1.id = pp.product_tmpl_id
                             JOIN product_category pc ON pc.id = ptp_1.categ_id
                             JOIN stock_lot ss ON ss.id = stm.lot_id
                             JOIN stock_picking sp ON sp.id = stm.picking_id AND sp.state::text = 'done'::text
                          JOIN stock_warehouse sw ON sw.id = stm.warehouse_id 
                      WHERE ss.id = stk.id and sw.x_is_bonded = TRUE))::double precision
                    END
                END::integer AS next1_net_ls,
            0 AS nvp_next2_receivable,
            0 AS sale_next2_unshipped,
                CASE
                    WHEN stk.bag_qty = 0::numeric THEN 0::double precision
                    ELSE sum(stk.init_qty)::integer::double precision +
                    CASE
                        WHEN (sct.no_of_pack - (( SELECT sum(stm.bag_no) AS sum
                           FROM stock_move_line stm
                             JOIN product_product pp ON pp.id = stm.product_id
                             JOIN product_template ptp_1 ON ptp_1.id = pp.product_tmpl_id
                             JOIN product_category pc ON pc.id = ptp_1.categ_id
                             JOIN stock_lot ss ON ss.id = stm.lot_id
                             JOIN stock_picking sp ON sp.id = stm.picking_id AND sp.state::text = 'done'::text
                             JOIN stock_warehouse sw ON sw.id = sp.warehouse_id
                             JOIN stock_move_line trm ON trm.picking_id = sp.id
                             JOIN s_contract pcon ON pcon.id = sp.pcontract_id
                             JOIN ned_certificate cert ON cert.id = pcon.certificate_id
                             JOIN s_period spe ON spe.id = pcon.shipt_month
                          WHERE ss.id = stk.id))::double precision) = 0::double precision OR (sct.p_qty - (( SELECT sum(stm.init_qty) AS sum
                           FROM stock_move_line stm
                             JOIN product_product pp ON pp.id = stm.product_id
                             JOIN product_template ptp_1 ON ptp_1.id = pp.product_tmpl_id
                             JOIN product_category pc ON pc.id = ptp_1.categ_id
                             JOIN stock_lot ss ON ss.id = stm.lot_id
                             JOIN stock_picking sp ON sp.id = stm.picking_id AND sp.state::text = 'done'::text
                          WHERE ss.id = stk.id))::double precision) < 0::double precision THEN 0::double precision
                        ELSE sct.p_qty - (( SELECT sum(stm.init_qty) AS sum
                           FROM stock_move_line stm
                             JOIN product_product pp ON pp.id = stm.product_id
                             JOIN product_template ptp_1 ON ptp_1.id = pp.product_tmpl_id
                             JOIN product_category pc ON pc.id = ptp_1.categ_id
                             JOIN stock_lot ss ON ss.id = stm.lot_id
                             JOIN stock_picking sp ON sp.id = stm.picking_id AND sp.state::text = 'done'::text
                          JOIN stock_warehouse sw ON sw.id = stm.warehouse_id 
                      WHERE ss.id = stk.id and sw.x_is_bonded = TRUE))::double precision
                    END
                END::integer AS next2_net_ls,
            0 AS nvp_next3_receivable,
            0 AS sale_next3_unshipped,
                CASE
                    WHEN stk.bag_qty = 0::numeric THEN 0::double precision
                    ELSE sum(stk.init_qty)::integer::double precision +
                    CASE
                        WHEN (sct.no_of_pack - (( SELECT sum(stm.bag_no) AS sum
                           FROM stock_move_line stm
                             JOIN product_product pp ON pp.id = stm.product_id
                             JOIN product_template ptp_1 ON ptp_1.id = pp.product_tmpl_id
                             JOIN product_category pc ON pc.id = ptp_1.categ_id
                             JOIN stock_lot ss ON ss.id = stm.lot_id
                             JOIN stock_picking sp ON sp.id = stm.picking_id AND sp.state::text = 'done'::text
                             JOIN stock_warehouse sw ON sw.id = sp.warehouse_id
                             JOIN stock_move_line trm ON trm.picking_id = sp.id
                             JOIN s_contract pcon ON pcon.id = sp.pcontract_id
                             JOIN ned_certificate cert ON cert.id = pcon.certificate_id
                             JOIN s_period spe ON spe.id = pcon.shipt_month
                          WHERE ss.id = stk.id))::double precision) = 0::double precision OR (sct.p_qty - (( SELECT sum(stm.init_qty) AS sum
                           FROM stock_move_line stm
                             JOIN product_product pp ON pp.id = stm.product_id
                             JOIN product_template ptp_1 ON ptp_1.id = pp.product_tmpl_id
                             JOIN product_category pc ON pc.id = ptp_1.categ_id
                             JOIN stock_lot ss ON ss.id = stm.lot_id
                             JOIN stock_picking sp ON sp.id = stm.picking_id AND sp.state::text = 'done'::text
                          WHERE ss.id = stk.id))::double precision) < 0::double precision THEN 0::double precision
                        ELSE sct.p_qty - (( SELECT sum(stm.init_qty) AS sum
                           FROM stock_move_line stm
                             JOIN product_product pp ON pp.id = stm.product_id
                             JOIN product_template ptp_1 ON ptp_1.id = pp.product_tmpl_id
                             JOIN product_category pc ON pc.id = ptp_1.categ_id
                             JOIN stock_lot ss ON ss.id = stm.lot_id
                             JOIN stock_picking sp ON sp.id = stm.picking_id AND sp.state::text = 'done'::text
                          JOIN stock_warehouse sw ON sw.id = stm.warehouse_id 
                      WHERE ss.id = stk.id and sw.x_is_bonded = TRUE))::double precision
                    END
                END::integer AS next3_net_ls,
            0 AS nvp_next4_receivable,
            0 AS sale_next4_unshipped,
                CASE
                    WHEN stk.bag_qty = 0::numeric THEN 0::double precision
                    ELSE sum(stk.init_qty)::integer::double precision +
                    CASE
                        WHEN (sct.no_of_pack - (( SELECT sum(stm.bag_no) AS sum
                           FROM stock_move_line stm
                             JOIN product_product pp ON pp.id = stm.product_id
                             JOIN product_template ptp_1 ON ptp_1.id = pp.product_tmpl_id
                             JOIN product_category pc ON pc.id = ptp_1.categ_id
                             JOIN stock_lot ss ON ss.id = stm.lot_id
                             JOIN stock_picking sp ON sp.id = stm.picking_id AND sp.state::text = 'done'::text
                             JOIN stock_warehouse sw ON sw.id = sp.warehouse_id
                             JOIN stock_move_line trm ON trm.picking_id = sp.id
                             JOIN s_contract pcon ON pcon.id = sp.pcontract_id
                             JOIN ned_certificate cert ON cert.id = pcon.certificate_id
                             JOIN s_period spe ON spe.id = pcon.shipt_month
                          WHERE ss.id = stk.id))::double precision) = 0::double precision OR (sct.p_qty - (( SELECT sum(stm.init_qty) AS sum
                           FROM stock_move_line stm
                             JOIN product_product pp ON pp.id = stm.product_id
                             JOIN product_template ptp_1 ON ptp_1.id = pp.product_tmpl_id
                             JOIN product_category pc ON pc.id = ptp_1.categ_id
                             JOIN stock_lot ss ON ss.id = stm.lot_id
                             JOIN stock_picking sp ON sp.id = stm.picking_id AND sp.state::text = 'done'::text
                          WHERE ss.id = stk.id))::double precision) < 0::double precision THEN 0::double precision
                        ELSE sct.p_qty - (( SELECT sum(stm.init_qty) AS sum
                           FROM stock_move_line stm
                             JOIN product_product pp ON pp.id = stm.product_id
                             JOIN product_template ptp_1 ON ptp_1.id = pp.product_tmpl_id
                             JOIN product_category pc ON pc.id = ptp_1.categ_id
                             JOIN stock_lot ss ON ss.id = stm.lot_id
                             JOIN stock_picking sp ON sp.id = stm.picking_id AND sp.state::text = 'done'::text
                          JOIN stock_warehouse sw ON sw.id = stm.warehouse_id 
                      WHERE ss.id = stk.id and sw.x_is_bonded = TRUE))::double precision
                    END
                END::integer AS next4_net_ls,
            0 AS nvp_next5_receivable,
            0 AS sale_next5_unshipped,
                CASE
                    WHEN stk.bag_qty = 0::numeric THEN 0::double precision
                    ELSE sum(stk.init_qty)::integer::double precision +
                    CASE
                        WHEN (sct.no_of_pack - (( SELECT sum(stm.bag_no) AS sum
                           FROM stock_move_line stm
                             JOIN product_product pp ON pp.id = stm.product_id
                             JOIN product_template ptp_1 ON ptp_1.id = pp.product_tmpl_id
                             JOIN product_category pc ON pc.id = ptp_1.categ_id
                             JOIN stock_lot ss ON ss.id = stm.lot_id
                             JOIN stock_picking sp ON sp.id = stm.picking_id AND sp.state::text = 'done'::text
                             JOIN stock_warehouse sw ON sw.id = sp.warehouse_id
                             JOIN stock_move_line trm ON trm.picking_id = sp.id
                             JOIN s_contract pcon ON pcon.id = sp.pcontract_id
                             JOIN ned_certificate cert ON cert.id = pcon.certificate_id
                             JOIN s_period spe ON spe.id = pcon.shipt_month
                          WHERE ss.id = stk.id))::double precision) = 0::double precision OR (sct.p_qty - (( SELECT sum(stm.init_qty) AS sum
                           FROM stock_move_line stm
                             JOIN product_product pp ON pp.id = stm.product_id
                             JOIN product_template ptp_1 ON ptp_1.id = pp.product_tmpl_id
                             JOIN product_category pc ON pc.id = ptp_1.categ_id
                             JOIN stock_lot ss ON ss.id = stm.lot_id
                             JOIN stock_picking sp ON sp.id = stm.picking_id AND sp.state::text = 'done'::text
                          WHERE ss.id = stk.id))::double precision) < 0::double precision THEN 0::double precision
                        ELSE sct.p_qty - (( SELECT sum(stm.init_qty) AS sum
                           FROM stock_move_line stm
                             JOIN product_product pp ON pp.id = stm.product_id
                             JOIN product_template ptp_1 ON ptp_1.id = pp.product_tmpl_id
                             JOIN product_category pc ON pc.id = ptp_1.categ_id
                             JOIN stock_lot ss ON ss.id = stm.lot_id
                             JOIN stock_picking sp ON sp.id = stm.picking_id AND sp.state::text = 'done'::text
                          JOIN stock_warehouse sw ON sw.id = stm.warehouse_id 
                      WHERE ss.id = stk.id and sw.x_is_bonded = TRUE))::double precision
                    END
                END::integer AS next5_net_ls,
            0 AS nvp_next6_receivable,
            0 AS sale_next6_unshipped,
                CASE
                    WHEN stk.bag_qty = 0::numeric THEN 0::double precision
                    ELSE sum(stk.init_qty)::integer::double precision +
                    CASE
                        WHEN (sct.no_of_pack - (( SELECT sum(stm.bag_no) AS sum
                           FROM stock_move_line stm
                             JOIN product_product pp ON pp.id = stm.product_id
                             JOIN product_template ptp_1 ON ptp_1.id = pp.product_tmpl_id
                             JOIN product_category pc ON pc.id = ptp_1.categ_id
                             JOIN stock_lot ss ON ss.id = stm.lot_id
                             JOIN stock_picking sp ON sp.id = stm.picking_id AND sp.state::text = 'done'::text
                             JOIN stock_warehouse sw ON sw.id = sp.warehouse_id
                             JOIN stock_move_line trm ON trm.picking_id = sp.id
                             JOIN s_contract pcon ON pcon.id = sp.pcontract_id
                             JOIN ned_certificate cert ON cert.id = pcon.certificate_id
                             JOIN s_period spe ON spe.id = pcon.shipt_month
                          WHERE ss.id = stk.id))::double precision) = 0::double precision OR (sct.p_qty - (( SELECT sum(stm.init_qty) AS sum
                           FROM stock_move_line stm
                             JOIN product_product pp ON pp.id = stm.product_id
                             JOIN product_template ptp_1 ON ptp_1.id = pp.product_tmpl_id
                             JOIN product_category pc ON pc.id = ptp_1.categ_id
                             JOIN stock_lot ss ON ss.id = stm.lot_id
                             JOIN stock_picking sp ON sp.id = stm.picking_id AND sp.state::text = 'done'::text
                          WHERE ss.id = stk.id))::double precision) < 0::double precision THEN 0::double precision
                        ELSE sct.p_qty - (( SELECT sum(stm.init_qty) AS sum
                           FROM stock_move_line stm
                             JOIN product_product pp ON pp.id = stm.product_id
                             JOIN product_template ptp_1 ON ptp_1.id = pp.product_tmpl_id
                             JOIN product_category pc ON pc.id = ptp_1.categ_id
                             JOIN stock_lot ss ON ss.id = stm.lot_id
                             JOIN stock_picking sp ON sp.id = stm.picking_id AND sp.state::text = 'done'::text
                          JOIN stock_warehouse sw ON sw.id = stm.warehouse_id 
                      WHERE ss.id = stk.id and sw.x_is_bonded = TRUE))::double precision
                    END
                END::integer AS next6_net_ls,
            0 AS inactive,
            0 AS faq_derivable,
            now() AS update_at
           FROM stock_lot stk
             JOIN product_product ppp ON ppp.id = stk.product_id
             JOIN product_template ptp ON ptp.id = ppp.product_tmpl_id
             JOIN product_category ctg ON ctg.id = ptp.categ_id
             LEFT JOIN s_contract sct ON sct.id = stk.p_contract_id
             LEFT JOIN s_period ped ON ped.id = sct.shipt_month
          WHERE stk.active = true AND stk.is_bonded = true AND stk.init_qty > 0::numeric
          GROUP BY ctg.name, stk.name, stk.id, ppp.default_code, stk.bag_qty, ppp.id, sct.name, sct.p_qty, sct.no_of_pack
        UNION ALL
         SELECT row_number() OVER () AS id,
            pc.name AS prod_group,
            pp.default_code AS product,
            pp.id AS product_id,
            0 AS sitting_stock,
            0 AS npe_received_unfixed,
            0 AS gross_ls,
            sc.quantity AS nvp_receivable,
            0 AS unshipped_qty,
            sc.quantity AS net_ls,
            0 AS nvp_next1_receivable,
            0 AS sale_next1_unshipped,
            sc.quantity::integer AS next1_net_ls,
            0 AS nvp_next2_receivable,
            0 AS sale_next2_unshipped,
            sc.quantity::integer AS next2_net_ls,
            0 AS nvp_next3_receivable,
            0 AS sale_next3_unshipped,
            sc.quantity::integer AS next3_net_ls,
            0 AS nvp_next4_receivable,
            0 AS sale_next4_unshipped,
            sc.quantity::integer AS next4_net_ls,
            0 AS nvp_next5_receivable,
            0 AS sale_next5_unshipped,
            sc.quantity::integer AS next5_net_ls,
            0 AS nvp_next6_receivable,
            0 AS sale_next6_unshipped,
            sc.quantity::integer AS next6_net_ls,
            0 AS inactive,
            0 AS faq_derivable,
            now() AS update_at
           FROM x_unallocated_pcontract sc
             JOIN s_period spe ON spe.id = sc.ship_month_id
             JOIN product_product pp ON pp.id = sc.product_id
             JOIN product_template pt ON pt.id = pp.product_tmpl_id
             JOIN product_category pc ON pc.id = pt.categ_id
          WHERE spe.date_from = (( SELECT to_date(concat(date_part('year'::text, now())::character varying(255), '-', ltrim(to_char(date_part('month'::text, now()), '00'::text)), '-', '01'), 'YYYY-MM-DD'::text) AS to_date))
        UNION ALL
         SELECT row_number() OVER () AS id,
            pc.name AS prod_group,
            pp.default_code AS product,
            pp.id AS product_id,
            0 AS sitting_stock,
            0 AS npe_received_unfixed,
            0 AS gross_ls,
            0 AS nvp_receivable,
            0 AS unshipped_qty,
            0::double precision AS net_ls,
            sc.quantity::integer AS nvp_next1_receivable,
            0 AS sale_next1_unshipped,
            sc.quantity::integer AS next1_net_ls,
            0 AS nvp_next2_receivable,
            0 AS sale_next2_unshipped,
            0 AS next2_net_ls,
            0 AS nvp_next3_receivable,
            0 AS sale_next3_unshipped,
            sc.quantity::integer AS next3_net_ls,
            0 AS nvp_next4_receivable,
            0 AS sale_next4_unshipped,
            sc.quantity::integer AS next4_net_ls,
            0 AS nvp_next5_receivable,
            0 AS sale_next5_unshipped,
            sc.quantity::integer AS next5_net_ls,
            0 AS nvp_next6_receivable,
            0 AS sale_next6_unshipped,
            sc.quantity::integer AS next6_net_ls,
            0 AS inactive,
            0 AS faq_derivable,
            now() AS update_at
           FROM x_unallocated_pcontract sc
             JOIN s_period spe ON spe.id = sc.ship_month_id
             JOIN product_product pp ON pp.id = sc.product_id
             JOIN product_template pt ON pt.id = pp.product_tmpl_id
             JOIN product_category pc ON pc.id = pt.categ_id
          WHERE spe.date_from = (( SELECT to_date(concat(date_part('year'::text, now())::character varying(255), '-', ltrim(to_char(date_part('month'::text, now())+1, '00'::text)), '-', '01'), 'YYYY-MM-DD'::text) AS to_date))
        UNION ALL
         SELECT row_number() OVER () AS id,
            pc.name AS prod_group,
            pp.default_code AS product,
            pp.id AS product_id,
            0 AS sitting_stock,
            0 AS npe_received_unfixed,
            0 AS gross_ls,
            0 AS nvp_receivable,
            0 AS unshipped_qty,
            0::double precision AS net_ls,
            0 AS nvp_next1_receivable,
            0 AS sale_next1_unshipped,
            0 AS next1_net_ls,
            sc.quantity::integer AS nvp_next2_receivable,
            0 AS sale_next2_unshipped,
            sc.quantity::integer AS next2_net_ls,
            0 AS nvp_next3_receivable,
            0 AS sale_next3_unshipped,
            sc.quantity::integer AS next3_net_ls,
            0 AS nvp_next4_receivable,
            0 AS sale_next4_unshipped,
            sc.quantity::integer AS next4_net_ls,
            0 AS nvp_next5_receivable,
            0 AS sale_next5_unshipped,
            sc.quantity::integer AS next5_net_ls,
            0 AS nvp_next6_receivable,
            0 AS sale_next6_unshipped,
            sc.quantity::integer AS next6_net_ls,
            0 AS inactive,
            0 AS faq_derivable,
            now() AS update_at
           FROM x_unallocated_pcontract sc
             JOIN s_period spe ON spe.id = sc.ship_month_id
             JOIN product_product pp ON pp.id = sc.product_id
             JOIN product_template pt ON pt.id = pp.product_tmpl_id
             JOIN product_category pc ON pc.id = pt.categ_id
          WHERE spe.date_from = (( SELECT to_date(concat(date_part('year'::text, now())::character varying(255), '-', ltrim(to_char(date_part('month'::text, now())+2, '00'::text)), '-', '01'), 'YYYY-MM-DD'::text) AS to_date))
        UNION ALL
         SELECT row_number() OVER () AS id,
            pc.name AS prod_group,
            pp.default_code AS product,
            pp.id AS product_id,
            0 AS sitting_stock,
            0 AS npe_received_unfixed,
            0 AS gross_ls,
            0 AS nvp_receivable,
            0 AS unshipped_qty,
            0::double precision AS net_ls,
            0 AS nvp_next1_receivable,
            0 AS sale_next1_unshipped,
            0 AS next1_net_ls,
            0 AS nvp_next2_receivable,
            0 AS sale_next2_unshipped,
            0 AS next2_net_ls,
            sc.quantity::integer AS nvp_next3_receivable,
            0 AS sale_next3_unshipped,
            sc.quantity::integer AS next3_net_ls,
            0 AS nvp_next4_receivable,
            0 AS sale_next4_unshipped,
            sc.quantity::integer AS next4_net_ls,
            0 AS nvp_next5_receivable,
            0 AS sale_next5_unshipped,
            sc.quantity::integer AS next5_net_ls,
            0 AS nvp_next6_receivable,
            0 AS sale_next6_unshipped,
            sc.quantity::integer AS next6_net_ls,
            0 AS inactive,
            0 AS faq_derivable,
            now() AS update_at
           FROM x_unallocated_pcontract sc
             JOIN s_period spe ON spe.id = sc.ship_month_id
             JOIN product_product pp ON pp.id = sc.product_id
             JOIN product_template pt ON pt.id = pp.product_tmpl_id
             JOIN product_category pc ON pc.id = pt.categ_id
          WHERE spe.date_from = (( SELECT to_date(concat(date_part('year'::text, now())::character varying(255), '-', ltrim(to_char(date_part('month'::text, now())+3, '00'::text)), '-', '01'), 'YYYY-MM-DD'::text) AS to_date))
        UNION ALL
         SELECT row_number() OVER () AS id,
            pc.name AS prod_group,
            pp.default_code AS product,
            pp.id AS product_id,
            0 AS sitting_stock,
            0 AS npe_received_unfixed,
            0 AS gross_ls,
            0 AS nvp_receivable,
            0 AS unshipped_qty,
            0::double precision AS net_ls,
            0 AS nvp_next1_receivable,
            0 AS sale_next1_unshipped,
            0 AS next1_net_ls,
            0 AS nvp_next2_receivable,
            0 AS sale_next2_unshipped,
            0 AS next2_net_ls,
            0 AS nvp_next3_receivable,
            0 AS sale_next3_unshipped,
            0 AS next3_net_ls,
            sc.quantity::integer AS nvp_next4_receivable,
            0 AS sale_next4_unshipped,
            sc.quantity::integer AS next4_net_ls,
            0 AS nvp_next5_receivable,
            0 AS sale_next5_unshipped,
            sc.quantity::integer AS next5_net_ls,
            0 AS nvp_next6_receivable,
            0 AS sale_next6_unshipped,
            sc.quantity::integer AS next6_net_ls,
            0 AS inactive,
            0 AS faq_derivable,
            now() AS update_at
           FROM x_unallocated_pcontract sc
             JOIN s_period spe ON spe.id = sc.ship_month_id
             JOIN product_product pp ON pp.id = sc.product_id
             JOIN product_template pt ON pt.id = pp.product_tmpl_id
             JOIN product_category pc ON pc.id = pt.categ_id
          WHERE spe.date_from = (( SELECT to_date(concat(date_part('year'::text, now())::character varying(255), '-', ltrim(to_char(date_part('month'::text, now())+4, '00'::text)), '-', '01'), 'YYYY-MM-DD'::text) AS to_date))
        UNION ALL
         SELECT row_number() OVER () AS id,
            pc.name AS prod_group,
            pp.default_code AS product,
            pp.id AS product_id,
            0 AS sitting_stock,
            0 AS npe_received_unfixed,
            0 AS gross_ls,
            0 AS nvp_receivable,
            0 AS unshipped_qty,
            0::double precision AS net_ls,
            0 AS nvp_next1_receivable,
            0 AS sale_next1_unshipped,
            0 AS next1_net_ls,
            0 AS nvp_next2_receivable,
            0 AS sale_next2_unshipped,
            0 AS next2_net_ls,
            0 AS nvp_next3_receivable,
            0 AS sale_next3_unshipped,
            0 AS next3_net_ls,
            0 AS nvp_next4_receivable,
            0 AS sale_next4_unshipped,
            0 AS next4_net_ls,
            sc.quantity::integer AS nvp_next5_receivable,
            0 AS sale_next5_unshipped,
            sc.quantity::integer AS next5_net_ls,
            0 AS nvp_next6_receivable,
            0 AS sale_next6_unshipped,
            sc.quantity::integer AS next6_net_ls,
            0 AS inactive,
            0 AS faq_derivable,
            now() AS update_at
           FROM x_unallocated_pcontract sc
             JOIN s_period spe ON spe.id = sc.ship_month_id
             JOIN product_product pp ON pp.id = sc.product_id
             JOIN product_template pt ON pt.id = pp.product_tmpl_id
             JOIN product_category pc ON pc.id = pt.categ_id
          WHERE spe.date_from = (( SELECT to_date(concat(date_part('year'::text, now())::character varying(255), '-', ltrim(to_char(date_part('month'::text, now())+5, '00'::text)), '-', '01'), 'YYYY-MM-DD'::text) AS to_date))
        UNION ALL
         SELECT row_number() OVER () AS id,
            pc.name AS prod_group,
            pp.default_code AS product,
            pp.id AS product_id,
            0 AS sitting_stock,
            0 AS npe_received_unfixed,
            0 AS gross_ls,
            0 AS nvp_receivable,
            0 AS unshipped_qty,
            0::double precision AS net_ls,
            0 AS nvp_next1_receivable,
            0 AS sale_next1_unshipped,
            0 AS next1_net_ls,
            0 AS nvp_next2_receivable,
            0 AS sale_next2_unshipped,
            0 AS next2_net_ls,
            0 AS nvp_next3_receivable,
            0 AS sale_next3_unshipped,
            0 AS next3_net_ls,
            0 AS nvp_next4_receivable,
            0 AS sale_next4_unshipped,
            0 AS next4_net_ls,
            0 AS nvp_next5_receivable,
            0 AS sale_next5_unshipped,
            0 AS next5_net_ls,
            sc.quantity::integer AS nvp_next6_receivable,
            0 AS sale_next6_unshipped,
            sc.quantity::integer AS next6_net_ls,
            0 AS inactive,
            0 AS faq_derivable,
            now() AS update_at
           FROM x_unallocated_pcontract sc
             JOIN s_period spe ON spe.id = sc.ship_month_id
             JOIN product_product pp ON pp.id = sc.product_id
             JOIN product_template pt ON pt.id = pp.product_tmpl_id
             JOIN product_category pc ON pc.id = pt.categ_id
          WHERE spe.date_from = (( SELECT to_date(concat(date_part('year'::text, now())::character varying(255), '-', ltrim(to_char(date_part('month'::text, now())+6, '00'::text)), '-', '01'), 'YYYY-MM-DD'::text) AS to_date))
        UNION ALL
         SELECT row_number() OVER () AS id,
            pc.name AS prod_group,
            pp.default_code AS product,
            pp.id AS product_id,
            0 AS sitting_stock,
            0 AS npe_received_unfixed,
            0 AS gross_ls,
            sc.p_qty AS nvp_receivable,
            sc.p_qty AS unshipped_qty,
            0 AS net_ls,
            0 AS nvp_next1_receivable,
            0 AS sale_next1_unshipped,
            0 AS next1_net_ls,
            0 AS nvp_next2_receivable,
            0 AS sale_next2_unshipped,
            0 AS next2_net_ls,
            0 AS nvp_next3_receivable,
            0 AS sale_next3_unshipped,
            0 AS next3_net_ls,
            0 AS nvp_next4_receivable,
            0 AS sale_next4_unshipped,
            0 AS next4_net_ls,
            0 AS nvp_next5_receivable,
            0 AS sale_next5_unshipped,
            0 AS next5_net_ls,
            0 AS nvp_next6_receivable,
            0 AS sale_next6_unshipped,
            0 AS next6_net_ls,
            0 AS inactive,
            0 AS faq_derivable,
            now() AS update_at
           FROM traffic_contract sc
             JOIN s_period spe ON spe.id = sc.shipt_month
             JOIN product_product pp ON pp.id = sc.standard_id
             JOIN product_template pt ON pt.id = pp.product_tmpl_id
             JOIN product_category pc ON pc.id = pt.categ_id
          WHERE sc.shipby_id = 22 AND sc.shipment_status::text <> 'Done'::text AND spe.date_from <= (( SELECT to_date(concat(date_part('year'::text, now())::character varying(255), '-', ltrim(to_char(date_part('month'::text, now()), '00'::text)), '-', '01'), 'YYYY-MM-DD'::text) AS to_date)) AND (sc.origin::text = ANY (ARRAY['VN'::character varying::text, 'LA'::character varying::text]))
        UNION ALL
         SELECT row_number() OVER () AS id,
            pc.name AS prod_group,
            pp.default_code AS product,
            pp.id AS product_id,
            0 AS sitting_stock,
            0 AS npe_received_unfixed,
            0 AS gross_ls,
            0 AS nvp_receivable,
            0 AS unshipped_qty,
            0 AS net_ls,
            sc.p_qty::integer AS nvp_next1_receivable,
            sc.p_qty::integer AS sale_next1_unshipped,
            0 AS next1_net_ls,
            0 AS nvp_next2_receivable,
            0 AS sale_next2_unshipped,
            0 AS next2_net_ls,
            0 AS nvp_next3_receivable,
            0 AS sale_next3_unshipped,
            0 AS next3_net_ls,
            0 AS nvp_next4_receivable,
            0 AS sale_next4_unshipped,
            0 AS next4_net_ls,
            0 AS nvp_next5_receivable,
            0 AS sale_next5_unshipped,
            0 AS next5_net_ls,
            0 AS nvp_next6_receivable,
            0 AS sale_next6_unshipped,
            0 AS next6_net_ls,
            0 AS inactive,
            0 AS faq_derivable,
            now() AS update_at
           FROM traffic_contract sc
             JOIN s_period spe ON spe.id = sc.shipt_month
             JOIN product_product pp ON pp.id = sc.standard_id
             JOIN product_template pt ON pt.id = pp.product_tmpl_id
             JOIN product_category pc ON pc.id = pt.categ_id
          WHERE sc.shipby_id = 22 AND sc.shipment_status::text <> 'Done'::text AND spe.date_from <= (( SELECT to_date(concat(date_part('year'::text, now())::character varying(255), '-', ltrim(to_char(date_part('month'::text, now())+1, '00'::text)), '-', '01'), 'YYYY-MM-DD'::text) AS to_date)) AND (sc.origin::text = ANY (ARRAY['VN'::character varying::text, 'LA'::character varying::text]))
        UNION ALL
         SELECT row_number() OVER () AS id,
            pc.name AS prod_group,
            pp.default_code AS product,
            pp.id AS product_id,
            0 AS sitting_stock,
            0 AS npe_received_unfixed,
            0 AS gross_ls,
            0 AS nvp_receivable,
            0 AS unshipped_qty,
            0 AS net_ls,
            0 AS nvp_next1_receivable,
            0 AS sale_next1_unshipped,
            0 AS next1_net_ls,
            sc.p_qty::integer AS nvp_next2_receivable,
            sc.p_qty::integer AS sale_next2_unshipped,
            0 AS next2_net_ls,
            0 AS nvp_next3_receivable,
            0 AS sale_next3_unshipped,
            0 AS next3_net_ls,
            0 AS nvp_next4_receivable,
            0 AS sale_next4_unshipped,
            0 AS next4_net_ls,
            0 AS nvp_next5_receivable,
            0 AS sale_next5_unshipped,
            0 AS next5_net_ls,
            0 AS nvp_next6_receivable,
            0 AS sale_next6_unshipped,
            0 AS next6_net_ls,
            0 AS inactive,
            0 AS faq_derivable,
            now() AS update_at
           FROM traffic_contract sc
             JOIN s_period spe ON spe.id = sc.shipt_month
             JOIN product_product pp ON pp.id = sc.standard_id
             JOIN product_template pt ON pt.id = pp.product_tmpl_id
             JOIN product_category pc ON pc.id = pt.categ_id
          WHERE sc.shipby_id = 22 AND sc.shipment_status::text <> 'Done'::text AND spe.date_from <= (( SELECT to_date(concat(date_part('year'::text, now())::character varying(255), '-', ltrim(to_char(date_part('month'::text, now())+2, '00'::text)), '-', '01'), 'YYYY-MM-DD'::text) AS to_date)) AND (sc.origin::text = ANY (ARRAY['VN'::character varying::text, 'LA'::character varying::text]))
        UNION ALL
         SELECT row_number() OVER () AS id,
            pc.name AS prod_group,
            pp.default_code AS product,
            pp.id AS product_id,
            0 AS sitting_stock,
            0 AS npe_received_unfixed,
            0 AS gross_ls,
            0 AS nvp_receivable,
            0 AS unshipped_qty,
            0 AS net_ls,
            0 AS nvp_next1_receivable,
            0 AS sale_next1_unshipped,
            0 AS next1_net_ls,
            0 AS nvp_next2_receivable,
            0 AS sale_next2_unshipped,
            0 AS next2_net_ls,
            sc.p_qty::integer AS nvp_next3_receivable,
            sc.p_qty::integer AS sale_next3_unshipped,
            0 AS next3_net_ls,
            0 AS nvp_next4_receivable,
            0 AS sale_next4_unshipped,
            0 AS next4_net_ls,
            0 AS nvp_next5_receivable,
            0 AS sale_next5_unshipped,
            0 AS next5_net_ls,
            0 AS nvp_next6_receivable,
            0 AS sale_next6_unshipped,
            0 AS next6_net_ls,
            0 AS inactive,
            0 AS faq_derivable,
            now() AS update_at
           FROM traffic_contract sc
             JOIN s_period spe ON spe.id = sc.shipt_month
             JOIN product_product pp ON pp.id = sc.standard_id
             JOIN product_template pt ON pt.id = pp.product_tmpl_id
             JOIN product_category pc ON pc.id = pt.categ_id
          WHERE sc.shipby_id = 22 AND sc.shipment_status::text <> 'Done'::text AND spe.date_from <= (( SELECT to_date(concat(date_part('year'::text, now())::character varying(255), '-', ltrim(to_char(date_part('month'::text, now())+3, '00'::text)), '-', '01'), 'YYYY-MM-DD'::text) AS to_date)) AND (sc.origin::text = ANY (ARRAY['VN'::character varying::text, 'LA'::character varying::text]))
        UNION ALL
         SELECT row_number() OVER () AS id,
            pc.name AS prod_group,
            pp.default_code AS product,
            pp.id AS product_id,
            0 AS sitting_stock,
            0 AS npe_received_unfixed,
            0 AS gross_ls,
            0 AS nvp_receivable,
            0 AS unshipped_qty,
            0 AS net_ls,
            0 AS nvp_next1_receivable,
            0 AS sale_next1_unshipped,
            0 AS next1_net_ls,
            0 AS nvp_next2_receivable,
            0 AS sale_next2_unshipped,
            0 AS next2_net_ls,
            0 AS nvp_next3_receivable,
            0 AS sale_next3_unshipped,
            0 AS next3_net_ls,
            sc.p_qty::integer AS nvp_next4_receivable,
            sc.p_qty::integer AS sale_next4_unshipped,
            0 AS next4_net_ls,
            0 AS nvp_next5_receivable,
            0 AS sale_next5_unshipped,
            0 AS next5_net_ls,
            0 AS nvp_next6_receivable,
            0 AS sale_next6_unshipped,
            0 AS next6_net_ls,
            0 AS inactive,
            0 AS faq_derivable,
            now() AS update_at
           FROM traffic_contract sc
             JOIN s_period spe ON spe.id = sc.shipt_month
             JOIN product_product pp ON pp.id = sc.standard_id
             JOIN product_template pt ON pt.id = pp.product_tmpl_id
             JOIN product_category pc ON pc.id = pt.categ_id
          WHERE sc.shipby_id = 22 AND sc.shipment_status::text <> 'Done'::text AND spe.date_from <= (( SELECT to_date(concat(date_part('year'::text, now())::character varying(255), '-', ltrim(to_char(date_part('month'::text, now())+4, '00'::text)), '-', '01'), 'YYYY-MM-DD'::text) AS to_date)) AND (sc.origin::text = ANY (ARRAY['VN'::character varying::text, 'LA'::character varying::text]))
        UNION ALL
         SELECT row_number() OVER () AS id,
            pc.name AS prod_group,
            pp.default_code AS product,
            pp.id AS product_id,
            0 AS sitting_stock,
            0 AS npe_received_unfixed,
            0 AS gross_ls,
            0 AS nvp_receivable,
            0 AS unshipped_qty,
            0 AS net_ls,
            0 AS nvp_next1_receivable,
            0 AS sale_next1_unshipped,
            0 AS next1_net_ls,
            0 AS nvp_next2_receivable,
            0 AS sale_next2_unshipped,
            0 AS next2_net_ls,
            0 AS nvp_next3_receivable,
            0 AS sale_next3_unshipped,
            0 AS next3_net_ls,
            0 AS nvp_next4_receivable,
            0 AS sale_next4_unshipped,
            0 AS next4_net_ls,
            sc.p_qty::integer AS nvp_next5_receivable,
            sc.p_qty::integer AS sale_next5_unshipped,
            0 AS next5_net_ls,
            0 AS nvp_next6_receivable,
            0 AS sale_next6_unshipped,
            0 AS next6_net_ls,
            0 AS inactive,
            0 AS faq_derivable,
            now() AS update_at
           FROM traffic_contract sc
             JOIN s_period spe ON spe.id = sc.shipt_month
             JOIN product_product pp ON pp.id = sc.standard_id
             JOIN product_template pt ON pt.id = pp.product_tmpl_id
             JOIN product_category pc ON pc.id = pt.categ_id
          WHERE sc.shipby_id = 22 AND sc.shipment_status::text <> 'Done'::text AND spe.date_from <= (( SELECT to_date(concat(date_part('year'::text, now())::character varying(255), '-', ltrim(to_char(date_part('month'::text, now())+5, '00'::text)), '-', '01'), 'YYYY-MM-DD'::text) AS to_date)) AND (sc.origin::text = ANY (ARRAY['VN'::character varying::text, 'LA'::character varying::text]))
        UNION ALL
         SELECT row_number() OVER () AS id,
            pc.name AS prod_group,
            pp.default_code AS product,
            pp.id AS product_id,
            0 AS sitting_stock,
            0 AS npe_received_unfixed,
            0 AS gross_ls,
            0 AS nvp_receivable,
            0 AS unshipped_qty,
            0 AS net_ls,
            0 AS nvp_next1_receivable,
            0 AS sale_next1_unshipped,
            0 AS next1_net_ls,
            0 AS nvp_next2_receivable,
            0 AS sale_next2_unshipped,
            0 AS next2_net_ls,
            0 AS nvp_next3_receivable,
            0 AS sale_next3_unshipped,
            0 AS next3_net_ls,
            0 AS nvp_next4_receivable,
            0 AS sale_next4_unshipped,
            0 AS next4_net_ls,
            0 AS nvp_next5_receivable,
            0 AS sale_next5_unshipped,
            0 AS next5_net_ls,
            sc.p_qty::integer AS nvp_next6_receivable,
            sc.p_qty::integer AS sale_next6_unshipped,
            0 AS next6_net_ls,
            0 AS inactive,
            0 AS faq_derivable,
            now() AS update_at
           FROM traffic_contract sc
             JOIN s_period spe ON spe.id = sc.shipt_month
             JOIN product_product pp ON pp.id = sc.standard_id
             JOIN product_template pt ON pt.id = pp.product_tmpl_id
             JOIN product_category pc ON pc.id = pt.categ_id
          WHERE sc.shipby_id = 22 AND sc.shipment_status::text <> 'Done'::text AND spe.date_from <= (( SELECT to_date(concat(date_part('year'::text, now())::character varying(255), '-', ltrim(to_char(date_part('month'::text, now())+6, '00'::text)), '-', '01'), 'YYYY-MM-DD'::text) AS to_date)) AND (sc.origin::text = ANY (ARRAY['VN'::character varying::text, 'LA'::character varying::text]))
        UNION ALL
         SELECT row_number() OVER () AS id,
            pc.name AS prod_group,
            pp.default_code AS product,
            pp.id AS product_id,
            0 AS sitting_stock,
            0 AS npe_received_unfixed,
            0 AS gross_ls,
            ss.unreceived AS nvp_receivable,
            0 AS unshipped_qty,
            ss.unreceived AS net_ls,
            0 AS nvp_next1_receivable,
            0 AS sale_next1_unshipped,
            0 AS next1_net_ls,
            0 AS nvp_next2_receivable,
            0 AS sale_next2_unshipped,
            0 AS next2_net_ls,
            0 AS nvp_next3_receivable,
            0 AS sale_next3_unshipped,
            0 AS next3_net_ls,
            0 AS nvp_next4_receivable,
            0 AS sale_next4_unshipped,
            0 AS next4_net_ls,
            0 AS nvp_next5_receivable,
            0 AS sale_next5_unshipped,
            0 AS next5_net_ls,
            0 AS nvp_next6_receivable,
            0 AS sale_next6_unshipped,
            0 AS next6_net_ls,
            0 AS inactive,
            0 AS faq_derivable,
            now() AS update_at
           FROM stock_lot ss
             JOIN product_product pp ON pp.id = ss.product_id
             JOIN product_template pt ON pt.id = pp.product_tmpl_id
             JOIN product_category pc ON pc.id = pt.categ_id
          WHERE ss.is_bonded = true AND ss.warehouse_id <> 19
        UNION ALL
         SELECT row_number() OVER () AS id,
            pc.name AS prod_group,
            pp.default_code AS product,
            pp.id AS product_id,
            0 AS sitting_stock,
            0 AS npe_received_unfixed,
            0 AS gross_ls,
            0 AS nvp_receivable,
            0 AS unshipped_qty,
            0 AS net_ls,
            sc.p_qty::integer AS nvp_next1_receivable,
            0 AS sale_next1_unshipped,
            sc.p_qty::integer AS next1_net_ls,
            0 AS nvp_next2_receivable,
            0 AS sale_next2_unshipped,
            sc.p_qty::integer AS next2_net_ls,
            0 AS nvp_next3_receivable,
            0 AS sale_next3_unshipped,
            sc.p_qty::integer AS next3_net_ls,
            0 AS nvp_next4_receivable,
            0 AS sale_next4_unshipped,
            sc.p_qty::integer AS next4_net_ls,
            0 AS nvp_next5_receivable,
            0 AS sale_next5_unshipped,
            sc.p_qty::integer AS next5_net_ls,
            0 AS nvp_next6_receivable,
            0 AS sale_next6_unshipped,
            sc.p_qty::integer AS next6_net_ls,
            0 AS inactive,
            0 AS faq_derivable,
            now() AS update_at
           FROM s_contract sc
             JOIN s_period spe ON spe.id = sc.shipt_month
             JOIN product_product pp ON pp.id = sc.standard_id
             JOIN product_template pt ON pt.id = pp.product_tmpl_id
             JOIN product_category pc ON pc.id = pt.categ_id
          WHERE sc.type::text = 'p_contract'::text AND sc.x_is_bonded = true AND spe.date_from >= (( SELECT to_date(concat(date_part('year'::text, now())::character varying(255), '-', ltrim(to_char(date_part('month'::text, now()), '00'::text)), '-', '01'), 'YYYY-MM-DD'::text) AS to_date))
        UNION ALL
         SELECT row_number() OVER () AS id,
            pc.name AS prod_group,
            pp.default_code AS product,
            pp.id AS product_id,
            0 AS sitting_stock,
            0 AS npe_received_unfixed,
            0 AS gross_ls,
            0 AS nvp_receivable,
            0 AS unshipped_qty,
            0 AS net_ls,
            0 AS nvp_next1_receivable,
            0 AS sale_next1_unshipped,
            0 AS next1_net_ls,
            sc.p_qty::integer AS nvp_next2_receivable,
            0 AS sale_next2_unshipped,
            sc.p_qty::integer AS next2_net_ls,
            0 AS nvp_next3_receivable,
            0 AS sale_next3_unshipped,
            sc.p_qty::integer AS next3_net_ls,
            0 AS nvp_next4_receivable,
            0 AS sale_next4_unshipped,
            sc.p_qty::integer AS next4_net_ls,
            0 AS nvp_next5_receivable,
            0 AS sale_next5_unshipped,
            sc.p_qty::integer AS next5_net_ls,
            0 AS nvp_next6_receivable,
            0 AS sale_next6_unshipped,
            sc.p_qty::integer AS next6_net_ls,
            0 AS inactive,
            0 AS faq_derivable,
            now() AS update_at
           FROM s_contract sc
             JOIN s_period spe ON spe.id = sc.shipt_month
             JOIN product_product pp ON pp.id = sc.standard_id
             JOIN product_template pt ON pt.id = pp.product_tmpl_id
             JOIN product_category pc ON pc.id = pt.categ_id
          WHERE sc.type::text = 'p_contract'::text AND sc.x_is_bonded = true AND spe.date_from >= (( SELECT to_date(concat(date_part('year'::text, now())::character varying(255), '-', ltrim(to_char(date_part('month'::text, now())+1, '00'::text)), '-', '01'), 'YYYY-MM-DD'::text) AS to_date))
        UNION ALL
         SELECT row_number() OVER () AS id,
            pc.name AS prod_group,
            pp.default_code AS product,
            pp.id AS product_id,
            0 AS sitting_stock,
            0 AS npe_received_unfixed,
            0 AS gross_ls,
            0 AS nvp_receivable,
            0 AS unshipped_qty,
            0 AS net_ls,
            0 AS nvp_next1_receivable,
            0 AS sale_next1_unshipped,
            0 AS next1_net_ls,
            0 AS nvp_next2_receivable,
            0 AS sale_next2_unshipped,
            0 AS next2_net_ls,
            sc.p_qty::integer AS nvp_next3_receivable,
            0 AS sale_next3_unshipped,
            sc.p_qty::integer AS next3_net_ls,
            0 AS nvp_next4_receivable,
            0 AS sale_next4_unshipped,
            sc.p_qty::integer AS next4_net_ls,
            0 AS nvp_next5_receivable,
            0 AS sale_next5_unshipped,
            sc.p_qty::integer AS next5_net_ls,
            0 AS nvp_next6_receivable,
            0 AS sale_next6_unshipped,
            sc.p_qty::integer AS next6_net_ls,
            0 AS inactive,
            0 AS faq_derivable,
            now() AS update_at
           FROM s_contract sc
             JOIN s_period spe ON spe.id = sc.shipt_month
             JOIN product_product pp ON pp.id = sc.standard_id
             JOIN product_template pt ON pt.id = pp.product_tmpl_id
             JOIN product_category pc ON pc.id = pt.categ_id
          WHERE sc.type::text = 'p_contract'::text AND sc.x_is_bonded = true AND spe.date_from >= (( SELECT to_date(concat(date_part('year'::text, now())::character varying(255), '-', ltrim(to_char(date_part('month'::text, now())+2, '00'::text)), '-', '01'), 'YYYY-MM-DD'::text) AS to_date))
        UNION ALL
         SELECT row_number() OVER () AS id,
            pc.name AS prod_group,
            pp.default_code AS product,
            pp.id AS product_id,
            0 AS sitting_stock,
            0 AS npe_received_unfixed,
            0 AS gross_ls,
            0 AS nvp_receivable,
            0 AS unshipped_qty,
            0 AS net_ls,
            0 AS nvp_next1_receivable,
            0 AS sale_next1_unshipped,
            0 AS next1_net_ls,
            0 AS nvp_next2_receivable,
            0 AS sale_next2_unshipped,
            0 AS next2_net_ls,
            0 AS nvp_next3_receivable,
            0 AS sale_next3_unshipped,
            0 AS next3_net_ls,
            sc.p_qty::integer AS nvp_next4_receivable,
            0 AS sale_next4_unshipped,
            sc.p_qty::integer AS next4_net_ls,
            0 AS nvp_next5_receivable,
            0 AS sale_next5_unshipped,
            sc.p_qty::integer AS next5_net_ls,
            0 AS nvp_next6_receivable,
            0 AS sale_next6_unshipped,
            sc.p_qty::integer AS next6_net_ls,
            0 AS inactive,
            0 AS faq_derivable,
            now() AS update_at
           FROM s_contract sc
             JOIN s_period spe ON spe.id = sc.shipt_month
             JOIN product_product pp ON pp.id = sc.standard_id
             JOIN product_template pt ON pt.id = pp.product_tmpl_id
             JOIN product_category pc ON pc.id = pt.categ_id
          WHERE sc.type::text = 'p_contract'::text AND sc.x_is_bonded = true AND spe.date_from >= (( SELECT to_date(concat(date_part('year'::text, now())::character varying(255), '-', ltrim(to_char(date_part('month'::text, now())+3, '00'::text)), '-', '01'), 'YYYY-MM-DD'::text) AS to_date))
        UNION ALL
         SELECT row_number() OVER () AS id,
            pc.name AS prod_group,
            pp.default_code AS product,
            pp.id AS product_id,
            0 AS sitting_stock,
            0 AS npe_received_unfixed,
            0 AS gross_ls,
            0 AS nvp_receivable,
            0 AS unshipped_qty,
            0 AS net_ls,
            0 AS nvp_next1_receivable,
            0 AS sale_next1_unshipped,
            0 AS next1_net_ls,
            0 AS nvp_next2_receivable,
            0 AS sale_next2_unshipped,
            0 AS next2_net_ls,
            0 AS nvp_next3_receivable,
            0 AS sale_next3_unshipped,
            0 AS next3_net_ls,
            0 AS nvp_next4_receivable,
            0 AS sale_next4_unshipped,
            0 AS next4_net_ls,
            sc.p_qty::integer AS nvp_next5_receivable,
            0 AS sale_next5_unshipped,
            sc.p_qty::integer AS next5_net_ls,
            0 AS nvp_next6_receivable,
            0 AS sale_next6_unshipped,
            sc.p_qty::integer AS next6_net_ls,
            0 AS inactive,
            0 AS faq_derivable,
            now() AS update_at
           FROM s_contract sc
             JOIN s_period spe ON spe.id = sc.shipt_month
             JOIN product_product pp ON pp.id = sc.standard_id
             JOIN product_template pt ON pt.id = pp.product_tmpl_id
             JOIN product_category pc ON pc.id = pt.categ_id
          WHERE sc.type::text = 'p_contract'::text AND sc.x_is_bonded = true AND spe.date_from >= (( SELECT to_date(concat(date_part('year'::text, now())::character varying(255), '-', ltrim(to_char(date_part('month'::text, now())+4, '00'::text)), '-', '01'), 'YYYY-MM-DD'::text) AS to_date))
        UNION ALL
         SELECT row_number() OVER () AS id,
            pc.name AS prod_group,
            pp.default_code AS product,
            pp.id AS product_id,
            0 AS sitting_stock,
            0 AS npe_received_unfixed,
            0 AS gross_ls,
            0 AS nvp_receivable,
            0 AS unshipped_qty,
            0 AS net_ls,
            0 AS nvp_next1_receivable,
            0 AS sale_next1_unshipped,
            0 AS next1_net_ls,
            0 AS nvp_next2_receivable,
            0 AS sale_next2_unshipped,
            0 AS next2_net_ls,
            0 AS nvp_next3_receivable,
            0 AS sale_next3_unshipped,
            0 AS next3_net_ls,
            0 AS nvp_next4_receivable,
            0 AS sale_next4_unshipped,
            0 AS next4_net_ls,
            0 AS nvp_next5_receivable,
            0 AS sale_next5_unshipped,
            0 AS next5_net_ls,
            sc.p_qty::integer AS nvp_next6_receivable,
            0 AS sale_next6_unshipped,
            sc.p_qty::integer AS next6_net_ls,
            0 AS inactive,
            0 AS faq_derivable,
            now() AS update_at
           FROM s_contract sc
             JOIN s_period spe ON spe.id = sc.shipt_month
             JOIN product_product pp ON pp.id = sc.standard_id
             JOIN product_template pt ON pt.id = pp.product_tmpl_id
             JOIN product_category pc ON pc.id = pt.categ_id
          WHERE sc.type::text = 'p_contract'::text AND sc.x_is_bonded = true AND spe.date_from >= (( SELECT to_date(concat(date_part('year'::text, now())::character varying(255), '-', ltrim(to_char(date_part('month'::text, now())+5, '00'::text)), '-', '01'), 'YYYY-MM-DD'::text) AS to_date))) longshort
  GROUP BY longshort.prod_group, longshort.product, longshort.product_id, longshort.sitting_stock, longshort.npe_received_unfixed, longshort.gross_ls, longshort.nvp_receivable, longshort.unshipped_qty, longshort.net_ls, longshort.nvp_next1_receivable, longshort.sale_next1_unshipped, longshort.next1_net_ls, longshort.nvp_next2_receivable, longshort.sale_next2_unshipped, longshort.next2_net_ls, longshort.nvp_next3_receivable, longshort.sale_next3_unshipped, longshort.next3_net_ls, longshort.nvp_next4_receivable, longshort.sale_next4_unshipped, longshort.next4_net_ls, longshort.nvp_next5_receivable, longshort.sale_next5_unshipped, longshort.next5_net_ls, longshort.nvp_next6_receivable, longshort.sale_next6_unshipped, longshort.next6_net_ls, longshort.inactive, longshort.faq_derivable, longshort.update_at;
  """)
