# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import calendar
import datetime
from time import gmtime, strftime
DATE_FORMAT = "%Y-%m-%d"
# from odoo import tools
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

class VStockMaterial(models.Model):
    _name = 'v.stock.material'
    _description = 'V Stock Material'
    _auto = False
    
    name = fields.Char(string="Product", translate=True)
    default_code = fields.Char(string="Code")
    product_uom = fields.Char(string="Uom", translate=True)
    qty_in = fields.Float(string='Qty In',digits=(12,0))
    qty_out = fields.Float(string="Qty Out",digits=(12,0))

    qty_balance = fields.Float(string="Qty Balance",digits=(12,0))
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    # stock_material_line = fields.One2many('report.stock.material.line','line_out_id', string='Detail Out')
    # stock_material_out = fields.One2many('report.stock.material.line','line_in_id', string='Detail In')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
                    CREATE OR REPLACE VIEW public.v_stock_material AS
                      SELECT row_number() OVER (ORDER BY product_id DESC) AS id,
                        product_id as name,
                        default_code,
                        product_uom,
                        sum(qty_in) qty_in,
                        sum(qty_out) qty_out, 
                        sum(qty_in) - sum(qty_out) qty_balance,
                        warehouse_id
                FROM (
                        SELECT tmpl.name product_id,
                                pp.default_code default_code,
                                pu.name product_uom,
                                sum(sm.qty_done) qty_in,
                                0 qty_out,
                                sp.warehouse_id
                        FROM stock_move_line sm
                            JOIN stock_picking sp ON sm.picking_id = sp.id
                            JOIN product_product pp ON sm.product_id = pp.id
                            JOIN product_template tmpl ON tmpl.id = pp.product_tmpl_id
                            JOIN uom_uom pu ON pu.id = tmpl.uom_id
                            JOIN stock_picking_type spt on sp.picking_type_id =spt.id
                        WHERE sm.state = 'done'
                            AND spt.code = 'material_in'
                            --AND tmpl.type = 'consu'
                        GROUP BY tmpl.name,
                            pp.default_code,
                            pu.name,
                            spt.code,
                            sp.warehouse_id
                        UNION ALL 
                        SELECT tmpl.name product_id,
                                pp.default_code default_code,
                                pu.name product_uom,
                                0 qty_in,
                                sum(sm.qty_done) qty_out,
                                sp.warehouse_id
                        FROM stock_move_line sm
                            JOIN stock_picking sp ON sm.picking_id = sp.id
                            JOIN product_product pp ON sm.product_id = pp.id
                            JOIN product_template tmpl ON tmpl.id = pp.product_tmpl_id
                            JOIN uom_uom pu ON pu.id = tmpl.uom_id
                            JOIN stock_picking_type spt on sp.picking_type_id =spt.id
                        WHERE sm.state = 'done'
                            AND spt.code = 'material_out'
                            --AND tmpl.type = 'consu'
                        GROUP BY tmpl.name,
                            pp.default_code,
                            pu.name,
                            spt.code,
                            sp.warehouse_id
                        ) sm
                GROUP BY name,
                    default_code,
                    product_uom,
                    warehouse_id
                """)

    
    
    
    
    