# -*- coding: utf-8 -*-
from odoo import fields, models, tools


class CleanCoffeeReport(models.Model):
    _name = 'clean.coffee.report'
    _description = 'Clean Coffee Report'
    _auto = False

    product_id = fields.Many2one('product.product', string='Product')
    total_stock = fields.Float(string='Total Stock')
    total_dispatch = fields.Float(string='Total Dispatch')
    balance = fields.Float(string='Balance Stock')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'clean_coffee_report')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW clean_coffee_report AS (
                WITH clean_products AS (
                    SELECT pp.id AS product_id
                    FROM product_product pp
                    JOIN product_template pt ON pt.id = pp.product_tmpl_id
                    JOIN product_category pc ON pc.id = pt.categ_id
                    WHERE pt.template_qc = 'clean'
                      AND UPPER(pc.name) LIKE '%CLEAN%'
                ),
                stock_from_contract AS (
                    SELECT pc.product_id,
                           SUM(pc.qty_received_net) AS qty
                    FROM purchase_contract pc
                    JOIN ned_crop nc ON nc.id = pc.crop_id
                    WHERE pc.state NOT IN ('draft', 'cancel')
                      AND nc.state = 'current'
                      AND pc.product_id IN (SELECT product_id FROM clean_products)
                    GROUP BY pc.product_id
                ),
                stock_from_picking AS (
                    SELECT sp.product_id,
                           SUM(sp.total_init_qty) AS qty
                    FROM stock_picking sp
                    JOIN stock_picking_type spt ON spt.id = sp.picking_type_id
                    JOIN ned_crop nc ON nc.id = sp.crop_id
                    JOIN mrp_production mp ON mp.id = sp.production_id
                    JOIN mrp_bom mb ON mb.id = mp.bom_id
                    WHERE sp.state = 'done'
                      AND spt.code = 'production_in'
                      AND nc.state = 'current'
                      AND mb.code IN ('BTA1', 'BTA2', 'BTA4', 'BTA5')
                      AND sp.product_id IN (SELECT product_id FROM clean_products)
                    GROUP BY sp.product_id
                ),
                dispatch_from_picking AS (
                    SELECT sp.product_id,
                           SUM(sp.total_init_qty) AS qty
                    FROM stock_picking sp
                    JOIN stock_picking_type spt ON spt.id = sp.picking_type_id
                    JOIN ned_crop nc ON nc.id = sp.crop_id
                    WHERE sp.state = 'done'
                      AND spt.code = 'outgoing'
                      AND nc.state = 'current'
                      AND sp.product_id IN (SELECT product_id FROM clean_products)
                    GROUP BY sp.product_id
                )
                SELECT
                    cp.product_id AS id,
                    cp.product_id,
                    COALESCE(sc.qty, 0) + COALESCE(sp.qty, 0) AS total_stock,
                    COALESCE(dp.qty, 0) AS total_dispatch,
                    COALESCE(sc.qty, 0) + COALESCE(sp.qty, 0) - COALESCE(dp.qty, 0) AS balance
                FROM clean_products cp
                LEFT JOIN stock_from_contract sc ON sc.product_id = cp.product_id
                LEFT JOIN stock_from_picking sp ON sp.product_id = cp.product_id
                LEFT JOIN dispatch_from_picking dp ON dp.product_id = cp.product_id
                WHERE COALESCE(sc.qty, 0) + COALESCE(sp.qty, 0) > 0
                   OR COALESCE(dp.qty, 0) > 0
            )
        """)