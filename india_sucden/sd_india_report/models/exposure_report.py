# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict
import re

DATE_FORMAT = "%Y-%m-%d"


class ExposureReport(models.Model):
    _name = 'exposure.report'
    _description = 'Exposure Report'
    _auto = False

    product_id = fields.Many2one('product.product', string='Product')
    category_id = fields.Many2one('product.category', string='Category')
    template_qc = fields.Char(string='Template QC')
    bags_no = fields.Float(string='Contract Bags', digits=(12,0))
    quantity = fields.Float(string='Contract Qty', digits=(12,0))
    price = fields.Float(string='Contract Price', digits=(12,2))
    value = fields.Float(string='Contract Total Value', digits=(12,0))
    receive_gross_qty = fields.Float(string='Received Gross Qty', digits=(12,0))
    un_receive_gross_qty = fields.Float(string='UnReceived Gross Qty', digits=(12,0))
    un_receive_gross_value = fields.Float(string='UnReceived Gross Value', digits=(12,0))

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'exposure_report')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW exposure_report AS (
                SELECT
                    pc.product_id                       AS id,
                    pc.product_id                       AS product_id,
                    pt.categ_id                         AS category_id,
                    CASE
                        WHEN LOWER(categ.name) LIKE '%clean%' THEN 'Clean Coffee'
                        WHEN LOWER(categ.name) LIKE '%raw%'   THEN 'Raw Coffee'
                        WHEN pt.template_qc = 'raw'           THEN 'Raw Coffee'
                        WHEN pt.template_qc = 'clean'         THEN 'Clean Coffee'
                        ELSE NULL
                    END                                 AS template_qc,
                    SUM(pc.number_of_bags)              AS bags_no,
                    SUM(pc.total_qty)                   AS quantity,
                    SUM(pc.relation_price_unit)         AS price,
                    SUM(pc.amount_sub_total)            AS value,
                    SUM(pc.qty_received_net)            AS receive_gross_qty,
                    SUM(pc.qty_unreceived_net)          AS un_receive_gross_qty,
                    SUM(pc.unreceive_gross_value)       AS un_receive_gross_value
                FROM purchase_contract pc
                JOIN product_product pp   ON pp.id   = pc.product_id
                JOIN product_template pt  ON pt.id   = pp.product_tmpl_id
                JOIN product_category categ ON categ.id = pt.categ_id
                JOIN ned_crop nc          ON nc.id   = pc.crop_id
                WHERE pc.type = 'purchase' AND pc.origin IS NULL AND pc.state != 'cancel'
                    AND pc.qty_unreceived_net > 0
                    AND nc.state = 'current'
                GROUP BY
                    pc.product_id,
                    pt.categ_id,
                    categ.name,
                    pt.template_qc
            )
        """)