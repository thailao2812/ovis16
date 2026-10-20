# -*- coding: utf-8 -*-
from odoo import fields, models, tools


class PurchaseRawCoffeeReport(models.Model):
    _name = 'purchase.raw.coffee.report'
    _description = 'Purchase Raw Coffee Report'
    _auto = False

    name = fields.Char(string='Name')
    total_purchase_volume = fields.Float(string='Total Purchase Volume')
    avg_purchase_diff = fields.Float(string='Average Purchase Diff')
    ptbf_coffee = fields.Float(string='PTBF Coffee')
    total = fields.Float(string='Total Purchase + PTBF (Mt)')
    total_production = fields.Float(string='Total Production')
    balance = fields.Float(string='Balance Stock')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'purchase_raw_coffee_report')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW purchase_raw_coffee_report AS (
                WITH product_codes AS (
                    SELECT
                        pp.id AS product_id,
                        pp.default_code,
                        CASE pp.default_code
                            WHEN '11001' THEN 'Arabica Cherry (AC-Raw)'
                            WHEN '11002' THEN 'Arabica Parchment (AP-Raw)'
                            WHEN '11003' THEN 'Robusta Cherry (RC-Raw)'
                            WHEN '11005' THEN 'Robusta Parchment (RP-Raw)'
                            WHEN '12001' THEN 'Arabica Cherry EP (AC-EP)'
                            WHEN '12002' THEN 'Robusta Cherry EP (RC-EP)'
                        END AS name
                    FROM product_product pp
                    WHERE pp.default_code IN ('11001', '11002', '11003', '11005', '12001', '12002')
                ),
                total_purchase AS (
                    SELECT
                        pc.product_id,
                        SUM(pc.qty_received_net) AS qty
                    FROM purchase_contract pc
                    JOIN ned_crop nc ON nc.id = pc.crop_id
                    WHERE pc.type = 'purchase'
                      AND pc.state != 'cancel'
                      AND pc.qty_received_net > 0
                      AND nc.state = 'current'
                      AND pc.product_id IN (SELECT product_id FROM product_codes)
                    GROUP BY pc.product_id
                ),
                ptbf AS (
                    SELECT
                        pc.product_id,
                        SUM(pc.unfixed_gross_qty) AS qty
                    FROM purchase_contract pc
                    JOIN ned_crop nc ON nc.id = pc.crop_id
                    WHERE pc.type = 'consign'
                      AND pc.state != 'cancel'
                      AND pc.unfixed_gross_qty > 0
                      AND nc.state = 'current'
                      AND pc.product_id IN (SELECT product_id FROM product_codes)
                    GROUP BY pc.product_id
                ),
                total_production AS (
                    SELECT
                        sp.product_id,
                        SUM(sp.total_init_qty) AS qty
                    FROM stock_picking sp
                    JOIN stock_picking_type spt ON spt.id = sp.picking_type_id
                    JOIN ned_crop nc ON nc.id = sp.crop_id
                    JOIN mrp_production mp ON mp.id = sp.production_id
                    JOIN mrp_bom mb ON mb.id = mp.bom_id
                    WHERE spt.code = 'production_out'
                      AND sp.state = 'done'
                      AND nc.state = 'current'
                      AND mb.code IN ('BTA1', 'BTA2', 'BTA3', 'BTA4', 'BTA5', 'BTA6')
                      AND sp.product_id IN (SELECT product_id FROM product_codes)
                    GROUP BY sp.product_id
                ),
                avg_diff AS (
                    SELECT
                        cpp.product_id,
                        SUM(cpp.outturn_qty * CASE prd.default_code
                            WHEN '11001' THEN cpp.a_differential
                            WHEN '11002' THEN cpp.a_differential
                            WHEN '11003' THEN cpp.ab_differential
                            WHEN '11005' THEN cpp.ab_differential
                            WHEN '12001' THEN cpp.a_differential
                            WHEN '12002' THEN cpp.ab_differential
                        END) / NULLIF(SUM(cpp.outturn_qty), 0) AS avg_diff
                    FROM contract_price_purchase cpp
                    JOIN purchase_contract pc ON pc.id = cpp.contract_id
                    JOIN ned_crop nc ON nc.id = pc.crop_id
                    JOIN product_product prd ON prd.id = cpp.product_id
                    WHERE cpp.total_allocated_qty > 0
                      AND pc.state != 'cancel'
                      AND nc.state = 'current'
                      AND cpp.product_id IN (SELECT product_id FROM product_codes)
                    GROUP BY cpp.product_id
                )
                SELECT
                    pcd.product_id AS id,
                    pcd.name,
                    COALESCE(tp.qty, 0)                                    AS total_purchase_volume,
                    COALESCE(ad.avg_diff, 0)                               AS avg_purchase_diff,
                    COALESCE(pt.qty, 0)                                    AS ptbf_coffee,
                    COALESCE(tp.qty, 0) + COALESCE(pt.qty, 0)             AS total,
                    COALESCE(tprod.qty, 0)                                 AS total_production,
                    COALESCE(tp.qty, 0) + COALESCE(pt.qty, 0)
                        - COALESCE(tprod.qty, 0)                           AS balance
                FROM product_codes pcd
                LEFT JOIN total_purchase tp    ON tp.product_id    = pcd.product_id
                LEFT JOIN ptbf pt              ON pt.product_id    = pcd.product_id
                LEFT JOIN total_production tprod ON tprod.product_id = pcd.product_id
                LEFT JOIN avg_diff ad          ON ad.product_id    = pcd.product_id
            )
        """)