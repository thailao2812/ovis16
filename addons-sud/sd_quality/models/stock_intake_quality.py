# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from datetime import datetime

class QCIntakeQuality(models.Model):
    _name = 'v.qc.details'
    _description = 'QC Intake Quality'
    _auto =False

    zone = fields.Char(string = 'Zone')
    stack = fields.Char(string = 'Stack')
    stack_id = fields.Char(string = 'Stack id')
    balance_basis = fields.Float(string = 'Balance', digits=(12, 0))
    receipt_note = fields.Char(string = 'Receipt Note')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    receiving_date = fields.Date(string = 'Date')
    packing = fields.Char(string = 'Packing')
    mc = fields.Float(string = 'MC', group_operator = 'avg', digits=(12, 2))
    fm = fields.Float(string = 'FM', group_operator = 'avg', digits=(12, 2))
    black = fields.Float(string = 'Bl.', group_operator = 'avg', digits=(12, 2))
    broken = fields.Float(string = 'Brk.', group_operator = 'avg', digits=(12, 2))
    brown = fields.Float(string = 'Brw.', group_operator = 'avg', digits=(12, 2))
    mold = fields.Float(string = 'Mol.', group_operator = 'avg', digits=(12, 2))
    cherry = fields.Float(string = 'Chr.', group_operator = 'avg', digits=(12, 2))
    excelsa = fields.Float(string = 'Ex.', group_operator = 'avg', digits=(12, 2))
    screen20 = fields.Float(string = 'Scr20', group_operator = 'avg', digits=(12, 2))
    screen19 = fields.Float(string = 'Scr19', group_operator = 'avg', digits=(12, 2))
    screen18 = fields.Float(string = 'Scr18', group_operator = 'avg', digits=(12, 2))
    screen16 = fields.Float(string = 'Scr16', group_operator = 'avg', digits=(12, 2))
    screen13 = fields.Float(string = 'Scr13', group_operator = 'avg', digits=(12, 2))
    greatersc12 = fields.Float(string = 'Scr12', group_operator = 'avg', digits=(12, 2))
    belowsc12 = fields.Float(string = 'Bl-12', group_operator = 'avg', digits=(12, 2))
    burned = fields.Float(string = 'Burned', group_operator = 'avg', digits=(12, 2))
    eaten = fields.Float(string = 'Insect', group_operator = 'avg', digits=(12, 2))
    immature = fields.Float(string = 'Imt.', group_operator = 'avg', digits=(12, 2))
    product = fields.Char(string='Product')
    # receipt_qty = fields.Float(string="Receipt Qty.", digits=(12, 2))
    net_qty = fields.Float(string="Net Qty.", digits=(12, 0))
    basis_weight = fields.Float(string="Basis Qty.", digits=(12, 0))
    supplier = fields.Char(string = 'Supplier')
    supplier_id = fields.Char(string="Suppler Id")
    source_dis = fields.Char(string = 'District')
    source_province = fields.Char(string= 'Province')
    
    
    remark = fields.Char(string="Remark")
    x_inspectator = fields.Many2one('x_inspectors.kcs', string='Inspected / Sampler')
    sampler = fields.Char(string="Analysis By")
    bag_no = fields.Float(string="Bag nos.",digits=(12, 0))
    p_contract = fields.Char(string='P Contract')
    
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
        CREATE OR REPLACE VIEW public.v_qc_details AS
            SELECT row_number() OVER (ORDER BY (date(timezone('UTC',sp.date_done::timestamp)), sz.name, sc.name, sc.id , sp.name , sp.warehouse_id  ,
                rd.name , rcs.name ,
                np.name ,pp.default_code, rp.id ) DESC  ) AS id,
                sz.name AS zone,
                scon.name AS p_contract,
                sc.name AS stack,
                sc.id as stack_id,
                sc.init_qty AS balance_basis,
                sp.name AS receipt_note,
                sp.warehouse_id AS warehouse_id,
                date(timezone('UTC',sp.date_done::timestamp)) AS receiving_date,
                rd.name as source_dis,
                rcs.name as source_province,
                np.name AS packing,
                rkl.mc,
                rkl.fm,
                rkl.black,
                rkl.broken,
                rkl.brown,
                rkl.mold,
                rkl.cherry,
                rkl.excelsa,
                rkl.screen20,
                rkl.screen19,
                rkl.screen18,
                rkl.screen16,
                rkl.screen13,
                rkl.greatersc12,
                rkl.belowsc12,
                rkl.burned,
                rkl.eaten,
                rkl.immature,
                pp.default_code AS product,
                -- sm.product_uom_qty AS receipt_qty,
                rkl.product_qty net_qty,
                rkl.basis_weight basis_weight,
                rp.shortname AS supplier,
                rp.id as supplier_id,
                rkl.remark,
                
                rkl.x_inspectator,
                rkl.sampler,
                rkl.bag_no
                
                
            FROM stock_lot sc
                LEFT JOIN s_contract scon on scon.id = sc.p_contract_id
                LEFT JOIN stock_zone sz ON sz.id = sc.zone_id
                JOIN stock_picking sp ON sc.id = sp.lot_id
                LEFT JOIN stock_move_line sm ON sp.id = sm.picking_id
                LEFT JOIN ned_packing np ON sm.packing_id = np.id
                JOIN request_kcs_line rkl ON sp.id = rkl.picking_id
                JOIN product_product pp ON sm.product_id = pp.id
                LEFT JOIN res_partner rp ON sp.partner_id = rp.id
                LEFT JOIN res_district rd ON sp.districts_id=rd.id
                JOIN res_country_state rcs ON rd.state_id = rcs.id;
            """)