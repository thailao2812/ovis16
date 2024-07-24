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
    _name = 'v.fob.weight.franchise'
    _description = 'FOB Weight Franchise'
    _auto = False

    factory_etd = fields.Date(string = 'Factory ETD')
    # do_date = fields.Date(string = 'DO Date')
    si_name = fields.Char(sring = 'SI')
    customer = fields.Char(string = 'Customer')
    # p_contract = fields.Char(string = 'P-Contract')
    product_name = fields.Char(string = 'Product')
    description = fields.Char(string = 'Description')

    product_qty = fields.Float(string = 'Qty (Kg)', digits=(12, 0))
    # do_total_qty = fields.Float(string = 'DO Qty (Kg)', digits=(12, 0))
    gdn_weighbridge_qty = fields.Float(string = 'Qty Before (Kg)', digits=(12, 0))
    gdn_total_init_qty = fields.Float(string = 'Quantity (Kg)', digits=(12, 0))

    franchise_before_31072019 = fields.Float(string = 'Frch 31Jul2019_%', digits=(12, 2))
    franchise = fields.Float(string = 'Franchise_%', digits=(12, 2))
    franchise_out = fields.Char(string = 'Franchise Out')
    warehouse = fields.Many2one('stock.warehouse')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'v_fob_weight_franchise')
        self.env.cr.execute('''
            CREATE OR REPLACE VIEW public.v_fob_weight_franchise AS
            SELECT row_number() OVER (
                ORDER BY (
                    si.factory_etd,
                si.name ,
                rp.name ,
                pp.default_code,
                sil.name ,
               scgdn.warehouse_id
                   
                ) DESC  
            
            ) AS id,
                si.factory_etd,
                -- scgdn.deli_date as do_date,
                si.name si_name,
                rp.name customer,
                pp.default_code AS product_name,
                sil.name AS Description,
                scgdn.total_qty as product_qty,
                scgdn.gdn_weighbridge_qty,
                scgdn.gdn_total_init_qty,
                (scgdn.total_qty-scgdn.gdn_weighbridge_qty)/scgdn.total_qty*100 AS franchise_before_31072019,
                (scgdn.total_qty-scgdn.gdn_total_init_qty)/scgdn.total_qty*100 AS franchise,
                  CASE WHEN ((scgdn.total_qty-scgdn.gdn_weighbridge_qty)/scgdn.total_qty*100 < sct.allowed_franchise) OR
                    ((scgdn.total_qty-scgdn.gdn_total_init_qty)/scgdn.total_qty*100 < sct.allowed_franchise) then 'below'
                  ELSE (CASE WHEN ((scgdn.total_qty - scgdn.gdn_weighbridge_qty)/scgdn.total_qty*100 > sct.allowed_franchise + 0.1) OR
                    ((scgdn.total_qty - scgdn.gdn_total_init_qty)/scgdn.total_qty*100 > sct.allowed_franchise + 0.1) Then 'high' Else '' end)
                  END AS franchise_out,
                  scgdn.warehouse_id as warehouse
            FROM shipping_instruction si
                JOIN shipping_instruction_line sil ON si.id = sil.shipping_id
                JOIN product_product pp On sil.product_id = pp.id
                JOIN res_partner rp On si.partner_id = rp.id
                JOIN (SELECT sc.shipping_id,
                            sum(deli.gdn_weighbridge_qty) AS gdn_weighbridge_qty,
                            sum(deli.gdn_total_init_qty) AS gdn_total_init_qty,
                            -- deli.deli_date,
                            sum(deli.total_qty) AS total_qty,
                            deli.warehouse_id as warehouse_id
                    FROM sale_contract sc
                    JOIN (SELECT DLO.contract_id,
                                DLO.product_id,
                                -- DLO.deli_date,
                                SUM(DLO.total_weighbridge_qty) AS gdn_weighbridge_qty,
                                SUM(DLO.total_init_qty) AS gdn_total_init_qty,
                                SUM(DLO.total_qty) AS total_qty,
                                DLO.warehouse_id as warehouse_id
                          FROM (SELECT dlv.contract_id,
                                        dlv.product_id,
                                        dlv.total_qty,
                                        sp.name AS gdn_name,
                                        sp.total_init_qty,
                                        sp.total_weighbridge_qty,
                                        dlv.from_warehouse_id as warehouse_id
                                        -- dlv.date as deli_date
                                FROM delivery_order dlv
                                LEFT JOIN stock_picking sp ON dlv.picking_id=sp.id) DLO
                                GROUP BY DLO.contract_id, DLO.product_id, DLO.warehouse_id) deli ON sc.id=deli.contract_id  --, DLO.deli_date
                GROUP BY sc.shipping_id, deli.warehouse_id
                        -- deli.deli_date
                        ) scgdn ON sil.shipping_id=scgdn.shipping_id
                JOIN s_contract sct ON si.contract_id=sct.id
                WHERE sct.status='Factory'
                ORDER BY si.factory_etd desc
    ''')

