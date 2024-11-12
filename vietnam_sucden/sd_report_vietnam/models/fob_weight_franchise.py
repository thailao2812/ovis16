# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict

import time
from docutils.nodes import document
import calendar
import datetime
from time import gmtime, strftime
DATE_FORMAT = "%Y-%m-%d"

class FOB_Franchise(models.Model):
    _inherit = 'v.fob.weight.franchise'

    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    shipping_id = fields.Many2one('shipping.instruction', string='Shipping Name')
    partner_id = fields.Many2one('res.partner', string='Partner')
    product_id = fields.Many2one('product.product', string='Product')
    qty_si = fields.Float(string='Qty SI')
    ex_store_qty = fields.Float(string='Ex-stored Qty')
    invoice_qty = fields.Float(string='Invoice Qty')
    franchise_qty = fields.Float(string='Franchise Kg')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'v_fob_weight_franchise')
        self.env.cr.execute('''
            CREATE OR REPLACE VIEW public.v_fob_weight_franchise AS
            SELECT row_number() OVER (

                ORDER BY (
                    sw.id,
                    si.factory_etd,
                    si.id,
                    rp.id,
                    pp.id,
                    sil.name
                ) DESC  

            ) AS id,
                sw.id AS warehouse_id,
                si.factory_etd,
                si.id AS shipping_id,
                rp.id AS partner_id,
                pp.id AS product_id,
                sil.name AS description,
                MAX(si.total_line_qty) AS qty_si,
                SUM(deli.gdn_quantity) AS ex_store_qty,
                MAX(si.invoice_qty) AS invoice_qty,
                MAX(si.total_line_qty) - SUM(deli.gdn_quantity) AS franchise_qty,
                ((MAX(si.total_line_qty) - SUM(deli.gdn_quantity)) / MAX(si.total_line_qty)) * 100 AS franchise
            FROM
                shipping_instruction si
            JOIN
                s_contract sc ON sc.id = si.contract_id
            LEFT JOIN
                sale_contract nvs ON si.id = nvs.shipping_id
            LEFT JOIN (
                SELECT
                    dor.contract_id,
                    SUM(dol.product_qty) AS do_quantity,
                    SUM(sm.gdn_quantity) AS gdn_quantity,
                    sp.state
                FROM
                    delivery_order dor
                JOIN
                    delivery_order_line dol ON dor.id = dol.delivery_id
                LEFT JOIN
                    stock_picking sp ON dor.picking_id = sp.id
                LEFT JOIN (
                    SELECT
                        stock_move_line.picking_id,
                        SUM(stock_move_line.init_qty) AS gdn_quantity
                    FROM
                        stock_move_line
                    GROUP BY
                        stock_move_line.picking_id
                ) sm ON dor.picking_id = sm.picking_id
                WHERE
                    sp.state = 'done'
                GROUP BY
                    dor.contract_id, sp.state
            ) deli ON nvs.id = deli.contract_id
            LEFT JOIN
                stock_warehouse sw ON sw.id = si.warehouse_id
            JOIN
                res_partner rp ON si.partner_id = rp.id
            JOIN
                product_product pp ON si.product_id = pp.id
            JOIN
                shipping_instruction_line sil ON si.id = sil.shipping_id
            WHERE sc.status = 'Factory'
            GROUP BY
                si.id, sw.id, rp.id, pp.id, sil.name
                ''')



