# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict
import re
DATE_FORMAT = "%Y-%m-%d"
import datetime, time

from datetime import datetime


class Shipment_Quality(models.Model):
    _name = 'v.shipment.quality'
    _description = 'Shipment Quality Comparision'
    _auto = False

    scontract = fields.Char(string = 'Contract No.')
    partner = fields.Char(string = 'Customer')
    product = fields.Char(string = 'Product')
    quantity = fields.Float(string = 'Quantity (Kg)', digits=(12, 0))
    stack_name = fields.Char(string = 'Stack No.')
    shipment_date = fields.Date(string = 'Shipment date')
    mc_p = fields.Float(string = 'MC_Contract', digits=(12, 2))
    fm_p = fields.Float(string = 'FM_Contract', digits=(12, 2))
    bb_p = fields.Float(string = 'BB_Contract', digits=(12, 2))
    primary_scr_p = fields.Float(string = 'Contract Primary_Scr', digits=(12, 2))
    nvs_date = fields.Date(string = 'Despatch date')
    mc_qc = fields.Float(string = 'MC_Despatch', digits=(12, 2))
    fm_qc = fields.Float(string = 'FM_Despatch', digits=(12, 2))
    bb_qc = fields.Float(string = 'BB_Despatch', digits=(12, 2))
    primary_scr_qc = fields.Float(string = 'Despatch Primary_Scr', digits=(12, 2))

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'v_shipment_quality')
        self.env.cr.execute("""
                    CREATE OR REPLACE VIEW public.v_shipment_quality AS
                      SELECT row_number() OVER () AS id, rpt.* From (SELECT distinct rp.* From 
                        (select sc.name scontract, rp.name partner, scl.product_id, pp.default_code product, scl.product_qty quantity, sc.shipment_date, 
                        prm.name, prml.mc mc_p, prml.fm fm_p, prml.black + prml.broken as bb_p, 
                        CASE WHEN pc.name='G3' Then prml.screen13 + prml.screen16 + prml.screen18 + prml.screen19 + prml.screen20
                           WHEN pc.name='G13' Then prml.screen13 + prml.screen16 + prml.screen18 + prml.screen19 + prml.screen20
                           WHEN pc.name='G16' Then prml.screen16 + prml.screen18 + prml.screen19 + prml.screen20
                           WHEN pc.name='G18' Then prml.screen18 + prml.screen19 + prml.screen20
                          ELSE null End As primary_scr_p,
                          sale.date nvs_date, sca.stack_no, ss.name AS stack_name, lot.mc mc_qc, lot.fm fm_qc, lot.black + lot.broken as bb_qc,
                        CASE WHEN pc.name='G3' Then lot.screen13 + lot.screen16 + lot.screen18 + lot.screen19 + lot.screen20
                           WHEN pc.name='G13' Then lot.screen13 + lot.screen16 + lot.screen18 + lot.screen19 + lot.screen20
                           WHEN pc.name='G16' Then lot.screen16 + lot.screen18 + lot.screen19 + lot.screen20
                           WHEN pc.name='G18' Then lot.screen18 + lot.screen19 + lot.screen20
                          ELSE null End As primary_scr_qc
                        from s_contract sc
                        Join s_contract_line scl ON sc.id=scl.contract_id
                        JOIN res_partner rp ON rp.id=sc.partner_id
                        JOIN product_product pp ON pp.id=scl.product_id
                        JOIN product_template pt ON pp.product_tmpl_id=pt.id
                        JOIN product_category pc ON pt.categ_id=pc.id
                        JOIN ned_crop cr ON cr.id=sc.crop_id
                        JOIN mrp_bom_premium prm ON prm.crop_id=cr.id
                        Left JOIN mrp_bom_premium_line prml ON prml.prem_id=prm.id
                        JOIN sale_contract sale ON sale.scontract_id=sc.id
                        JOIN shipping_instruction si ON si.id=sale.shipping_id
                        JOIN stock_contract_allocation sca ON sca.shipping_id=si.id
                        JOIN stock_lot ss ON sca.stack_no=ss.id
                        JOIN (select sum(mc)/count(*) mc, sum(fm)/count(*) fm,sum(black)/count(*) black,sum(broken)/count(*) broken,
                            sum(screen13)/count(*) screen13,sum(screen16)/count(*) screen16,sum(screen18)/count(*) screen18,
                            sum(screen19)/count(*) screen19,sum(screen20)/count(*) screen20, contract_id from lot_kcs group by contract_id) lot 
                            ON lot.contract_id=sc.id
                        where scl.product_id=prml.product_id and sc.type='export' order by sc.id desc) As rp) As rpt
                    """)
