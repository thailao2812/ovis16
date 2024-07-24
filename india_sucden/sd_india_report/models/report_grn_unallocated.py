# -*- coding: utf-8 -*-
from odoo import api
from odoo import SUPERUSER_ID
from odoo import tools
from odoo import fields, models
from odoo.tools.translate import _
from odoo.exceptions import UserError
from datetime import datetime, timedelta, date
import time
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
from docutils.nodes import document
import calendar
import datetime
from time import gmtime, strftime
DATE_FORMAT = "%Y-%m-%d"


class ReportGRNUnallocated(models.Model):
    _name = 'report.grn.unallocated'
    _description = 'GRN Unallocated'
    _auto = False
    order = 'date_done desc'

    grade_id = fields.Many2one('product.category', string='Grade')
    unallocated = fields.Float(string='Unallocated')
    picking_id = fields.Many2one('stock.picking', string='GRN')
    date_done = fields.Datetime(string='Date of transfer')
    product_id = fields.Many2one('product.product', string='Product')
    origin = fields.Char(string='Origin')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
                    CREATE OR REPLACE VIEW public.report_grn_unallocated AS
                     SELECT row_number() OVER () AS id,
                        sp.id AS picking_id,
                        sp.date_done as date_done,
                        sp.product_id as product_id,
                        ctg.id as grade_id,
                        sp.origin as origin,
                        sp.qty_available as unallocated
                       FROM stock_picking sp
                         JOIN stock_picking_type spt ON sp.picking_type_id = spt.id
                         JOIN stock_move_line sm ON sp.id = sm.picking_id
                         JOIN product_product pp ON sm.product_id = pp.id
                         JOIN product_template pt ON pt.id = pp.product_tmpl_id
                         JOIN product_category ctg ON ctg.id = pt.categ_id
                         JOIN stock_warehouse sw on sw.id = sp.warehouse_id
                      WHERE (spt.code::text = ANY (ARRAY['incoming'::text])) 
                      AND ((spt.operation::text = ANY (ARRAY['factory'::text])) OR spt.operation is NULL)
                      AND sp.backorder_id is NULL and sp.qty_available > 0 and sp.state = 'done'
                      AND sp.origin not like '%FOT%' and ctg.parent_id = 27 and sp.name like '%GRN%'
                      AND sw.x_is_bonded = FALSE and sp.date_done >= '2020-01-10 00:00:00'
                      ORDER BY sp.date_done
        """)