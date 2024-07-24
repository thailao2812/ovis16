# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from datetime import datetime, date, timedelta

DATE_FORMAT = "%Y-%m-%d"
import calendar


class LongShortFactory(models.Model):
    _name = 'v.long.short.v3'
    _description = 'Long Short Factory'
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
    x_winp = fields.Float(string='Work In Progress')
    x_unallocate = fields.Float(string='Unallocated')

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
        tools.drop_view_if_exists(self.env.cr, 'v_long_short_v3')
        self.env.cr.execute("""
        CREATE OR REPLACE VIEW public.v_long_short_v3 AS SELECT row_number() OVER (
        order by (
                    v_longshort.prod_group,
                    v_longshort.product
                    ) DESC
        ) AS id,
      v_longshort.prod_group,
      v_longshort.product,
      v_longshort.product_id,
      v_longshort.sitting_stock,
      v_longshort.npe_received_unfixed,
      v_longshort.x_winp,
      v_longshort.x_unallocate,
      v_longshort.gross_ls,
      v_longshort.nvp_receivable,
      v_longshort.unshipped_qty,
      v_longshort.net_ls,
      v_longshort.nvp_next1_receivable,
      v_longshort.sale_next1_unshipped,
      v_longshort.next1_net_ls,
      v_longshort.nvp_next2_receivable,
      v_longshort.sale_next2_unshipped,
      v_longshort.next2_net_ls,
      v_longshort.nvp_next3_receivable,
      v_longshort.sale_next3_unshipped,
      v_longshort.next3_net_ls,
      v_longshort.nvp_next4_receivable,
      v_longshort.sale_next4_unshipped,
      v_longshort.next4_net_ls,
      v_longshort.nvp_next5_receivable,
      v_longshort.sale_next5_unshipped,
      v_longshort.next5_net_ls,
      v_longshort.nvp_next6_receivable,
      v_longshort.sale_next6_unshipped,
      v_longshort.next6_net_ls,
      v_longshort.inactive,
          CASE
              WHEN v_longshort.prod_group::text = 'G3'::text AND v_longshort.inactive <> 1::numeric THEN ( SELECT tmp.sitting_stock * 5::numeric / 100::numeric
                 FROM (( SELECT ctg.name AS prod_group,
                          ls.product,
                          ls.product_id,
                          ls.sitting_stock,
                          ls.npe_received_unfixed,
                          0 AS gross_ls,
                          ls.nvp_receivable,
                          ls.unshipped_qty,
                          0 AS net_ls,
                          ls.nvp_next1_receivable,
                          ls.sale_next1_unshipped,
                          0 AS next1_net_ls,
                          ls.nvp_next2_receivable,
                          ls.sale_next2_unshipped,
                          0 AS next2_net_ls,
                          ls.nvp_next3_receivable,
                          ls.sale_next3_unshipped,
                          0 AS next3_net_ls,
                          ls.nvp_next4_receivable,
                          ls.sale_next4_unshipped,
                          0 AS next4_net_ls,
                          ls.nvp_next5_receivable,
                          ls.sale_next5_unshipped,
                          0 AS next5_net_ls,
                          ls.nvp_next6_receivable,
                          ls.sale_next6_unshipped,
                          0 AS next6_net_ls,
                          ls.inactive,
                          ls.faq_derivable
                         FROM product_category ctg
                           JOIN product_template pt ON ctg.id = pt.categ_id
                           JOIN product_product pp ON pt.id = pp.product_tmpl_id
                           JOIN v_long_short ls ON pp.id = ls.product_id
                        WHERE (ctg.code::text <> ALL (ARRAY['NLTH'::character varying::text, 'DV'::character varying::text])) AND ls.inactive <> 0::numeric AND ctg.name::text = 'FAQ'::text
                        ORDER BY ctg.name)
                      UNION ALL
                      ( SELECT ctg.name AS prod_group,
                          ls.product,
                          ls.product_id,
                          ls.sitting_stock,
                          ls.npe_received_unfixed,
                          ls.gross_ls,
                          ls.nvp_receivable,
                          ls.unshipped_qty,
                          ls.net_ls,
                          ls.nvp_next1_receivable,
                          ls.sale_next1_unshipped,
                          ls.next1_net_ls,
                          ls.nvp_next2_receivable,
                          ls.sale_next2_unshipped,
                          ls.next2_net_ls,
                          ls.nvp_next3_receivable,
                          ls.sale_next3_unshipped,
                          ls.next3_net_ls,
                          ls.nvp_next4_receivable,
                          ls.sale_next4_unshipped,
                          ls.next4_net_ls,
                          ls.nvp_next5_receivable,
                          ls.sale_next5_unshipped,
                          ls.next5_net_ls,
                          ls.nvp_next6_receivable,
                          ls.sale_next6_unshipped,
                          ls.next6_net_ls,
                          ls.inactive,
                          ls.faq_derivable
                         FROM product_category ctg
                           JOIN product_template pt ON ctg.id = pt.categ_id
                           JOIN product_product pp ON pt.id = pp.product_tmpl_id
                           JOIN v_long_short ls ON pp.id = ls.product_id
                        WHERE (ctg.code::text <> ALL (ARRAY['NLTH'::character varying::text, 'DV'::character varying::text])) AND ls.inactive <> 0::numeric AND ctg.name::text <> 'FAQ'::text
                        ORDER BY ctg.name)) tmp
                WHERE tmp.prod_group::text = 'FAQ'::text)
              ELSE v_longshort.faq_derivable
          END AS faq_derivable,
      now() AS updated_at
     FROM (( SELECT ctg.name AS prod_group,
              ls.product,
              ls.product_id,
              ls.sitting_stock,
              ls.npe_received_unfixed,
              0 AS x_winp,
              0 AS x_unallocate,
              0 AS gross_ls,
              ls.nvp_receivable,
              ls.unshipped_qty,
              0 AS net_ls,
              ls.nvp_next1_receivable,
              ls.sale_next1_unshipped,
              0 AS next1_net_ls,
              ls.nvp_next2_receivable,
              ls.sale_next2_unshipped,
              0 AS next2_net_ls,
              ls.nvp_next3_receivable,
              ls.sale_next3_unshipped,
              0 AS next3_net_ls,
              ls.nvp_next4_receivable,
              ls.sale_next4_unshipped,
              0 AS next4_net_ls,
              ls.nvp_next5_receivable,
              ls.sale_next5_unshipped,
              0 AS next5_net_ls,
              ls.nvp_next6_receivable,
              ls.sale_next6_unshipped,
              0 AS next6_net_ls,
              ls.inactive,
              ls.faq_derivable
             FROM product_category ctg
               JOIN product_template pt ON ctg.id = pt.categ_id
               JOIN product_product pp ON pt.id = pp.product_tmpl_id
               JOIN v_long_short ls ON pp.id = ls.product_id
            WHERE (ctg.code::text <> ALL (ARRAY['NLTH'::character varying::text, 'DV'::character varying::text])) AND ls.inactive <> 0::numeric AND ctg.name::text = 'FAQ'::text
            ORDER BY ctg.name)
          UNION ALL
          ( SELECT ctg.name AS prod_group,
              ls.product,
              ls.product_id,
              ls.sitting_stock,
              ls.npe_received_unfixed,
              0 AS x_winp,
              0 AS x_unallocate,
              ls.gross_ls,
              ls.nvp_receivable,
              ls.unshipped_qty,
              ls.net_ls,
              ls.nvp_next1_receivable,
              ls.sale_next1_unshipped,
              ls.next1_net_ls,
              ls.nvp_next2_receivable,
              ls.sale_next2_unshipped,
              ls.next2_net_ls,
              ls.nvp_next3_receivable,
              ls.sale_next3_unshipped,
              ls.next3_net_ls,
              ls.nvp_next4_receivable,
              ls.sale_next4_unshipped,
              ls.next4_net_ls,
              ls.nvp_next5_receivable,
              ls.sale_next5_unshipped,
              ls.next5_net_ls,
              ls.nvp_next6_receivable,
              ls.sale_next6_unshipped,
              ls.next6_net_ls,
              ls.inactive,
              ls.faq_derivable
             FROM product_category ctg
               JOIN product_template pt ON ctg.id = pt.categ_id
               JOIN product_product pp ON pt.id = pp.product_tmpl_id
               JOIN v_long_short ls ON pp.id = ls.product_id
            WHERE (ctg.code::text <> ALL (ARRAY['NLTH'::character varying::text, 'DV'::character varying::text])) AND ls.inactive <> 0::numeric AND ctg.name::text <> 'FAQ'::text
            ORDER BY ctg.name)
          UNION ALL
           SELECT ctg.name AS prod_group,
              ''::character varying AS product,
              0 AS product_id,
              0 AS sitting_stock,
              0 AS npe_received_unfixed,
              batch.product_balance AS x_winp,
              0 AS x_unallocate,
              0 AS gross_ls,
              0 AS nvp_receivable,
              0 AS unshipped_qty,
              - batch.product_balance AS net_ls,
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
              0 AS faq_derivable
             FROM mrp_production batch
               JOIN product_category ctg ON batch.grade_id = ctg.id
               JOIN product_template pt ON ctg.id = pt.categ_id
               JOIN product_product pp ON pt.id = pp.product_tmpl_id
            WHERE (ctg.code::text <> ALL (ARRAY['NLTH'::character varying::text, 'DV'::character varying::text])) AND ctg.name::text <> 'FAQ'::text AND (batch.state::text = ANY (ARRAY['ready'::character varying::text, 'in_production'::character varying::text]))
           GROUP BY batch.name, ctg.name, batch.product_balance
          UNION ALL
           SELECT ctg.name AS prod_group,
              ''::character varying AS product,
              0 AS product_id,
              0 AS sitting_stock,
              0 AS npe_received_unfixed,
              0 AS x_winp,
              batch.unallocated AS x_unallocate,
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
              0 AS nvp_next6_receivable,
              0 AS sale_next6_unshipped,
              0 AS next6_net_ls,
              0 AS inactive,
              0 AS faq_derivable
             FROM report_grn_unallocated batch
               JOIN product_category ctg ON batch.grade_id = ctg.id
               JOIN product_template pt ON ctg.id = pt.categ_id
               JOIN product_product pp ON pt.id = pp.product_tmpl_id
            WHERE (ctg.code::text <> ALL (ARRAY['NLTH'::character varying::text, 'DV'::character varying::text])) AND ctg.name::text <> 'FAQ'::text
            GROUP BY ctg.name, batch.unallocated
          ) v_longshort;
        
        """)