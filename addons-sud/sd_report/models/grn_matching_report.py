# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict

from docutils.nodes import document
import calendar
import datetime
from time import gmtime, strftime
DATE_FORMAT = "%Y-%m-%d"

class GRNMatchingReport(models.Model):
    _name = 'v.grn.matching'
    _description = 'GRN Matching Report'
    _auto = False

    branch_id = fields.Char(sring = 'ID')
    grn_branch = fields.Char(sring = 'GRN Branch')
    shortname = fields.Char(sring = 'Partner')
    branch_date_received = fields.Datetime(string = 'Br. Date')
    grn_factory = fields.Char(sring = 'GRN Factory')
    truck_com = fields.Char(sring = 'Trucking Co.')
    factory_date_received = fields.Datetime(string = 'Factory Date')
    deduction_branch = fields.Float(string = 'Br. deduction (%)', digits=(12, 2), group_operator="avg")
    deduction_factory = fields.Float(string = 'Factory deduction (%)', digits=(12, 2), group_operator="avg")
    brn_fac = fields.Float(string = 'Var. (%)', digits=(12, 2), group_operator="avg")
    deficit = fields.Char(sring = 'Var. (%)')

    net_weight_branch = fields.Float(string = 'Br. Net (kg)', digits=(12, 0))
    net_weight_factory = fields.Float(string = 'Factory Net (kg)', digits=(12, 0))
    net_weight_deficit = fields.Float(string = 'Net +/- (kg)', digits=(12, 0))
    net_var = fields.Float(string = 'Net +/- (%)', digits=(12, 2))

    basis_weight_branch = fields.Float(string = 'Br. Basis (kg)', digits=(12, 0))
    basis_weight_factory = fields.Float(string = 'Factory Basis (kg)', digits=(12, 0))
    basis_weight_deficit = fields.Float(string = 'Basis +/- (kg)', digits=(12, 0))
    basis_var = fields.Float(string = 'Basis +/- (%)', digits=(12, 2))

    mc_branch = fields.Float(string = 'MC_%', digits=(12, 2))
    mc_factory = fields.Float(string = 'MC_%', digits=(12, 2))
    fm_branch = fields.Float(string = 'FM_%', digits=(12, 2))
    fm_factory = fields.Float(string = 'FM_%', digits=(12, 2))
    black_branch = fields.Float(string = 'Black_%', digits=(12, 2))
    black_factory = fields.Float(string = 'Black_%', digits=(12, 2))
    broken_branch = fields.Float(string = 'Broken_%', digits=(12, 2))
    broken_factory = fields.Float(string = 'Broken_%', digits=(12, 2))

    brown_branch = fields.Float(string = 'Brown_%', digits=(12, 2))
    brown_factory = fields.Float(string = 'Brown_%', digits=(12, 2))
    mold_branch = fields.Float(string = 'Mold_%', digits=(12, 2))
    mold_factory = fields.Float(string = 'Mold_%', digits=(12, 2))
    cherry_branch = fields.Float(string = 'Cherry_%', digits=(12, 2))
    cherry_factory = fields.Float(string = 'Cherry_%', digits=(12, 2))
    excelsa_branch = fields.Float(string = 'Excelsa_%', digits=(12, 2))
    excelsa_factory = fields.Float(string = 'Excelsa_%', digits=(12, 2))
    screen20_branch = fields.Float(string = 'Screen20_%', digits=(12, 2))
    screen20_factory = fields.Float(string = 'Screen20_%', digits=(12, 2))
    screen19_branch = fields.Float(string = 'Screen19_%', digits=(12, 2))
    screen19_factory = fields.Float(string = 'Screen19_%', digits=(12, 2))
    screen18_branch = fields.Float(string = 'Screen18_%', digits=(12, 2))
    screen18_factory = fields.Float(string = 'Screen18_%', digits=(12, 2))
    screen16_branch = fields.Float(string = 'Screen16_%', digits=(12, 2))
    screen16_factory = fields.Float(string = 'Screen16_%', digits=(12, 2))
    screen13_branch = fields.Float(string = 'Screen13_%', digits=(12, 2))
    screen13_factory = fields.Float(string = 'Screen13_%', digits=(12, 2))
    belowsc12_branch = fields.Float(string = 'Belowsc12_%', digits=(12, 2))
    belowsc12_factory = fields.Float(string = 'Belowsc12_%', digits=(12, 2))
    burned_branch = fields.Float(string = 'Burned_%', digits=(12, 2))
    burned_factory = fields.Float(string = 'Burned_%', digits=(12, 2))
    eaten_branch = fields.Float(string = 'Insect_%', digits=(12, 2))
    eaten_factory = fields.Float(string = 'Insect_%', digits=(12, 2))
    immature_branch = fields.Float(string = 'Immature_%', digits=(12, 2))
    immature_factory = fields.Float(string = 'Immature_%', digits=(12, 2))
    vehicle_no = fields.Char(string = 'Truck no.')
    product = fields.Char(string = 'Product')
    x_inspectator = fields.Char(string='Inspectors')

    # mc_var field temporarily stores variance between MC at buying station and destination WH, 
    # function compute to compute varianice and return to mc_var
    mc_var = fields.Float(compute = '_compute_mc')

    @api.depends('mc_branch', 'mc_factory')
    def _compute_mc(self):
        self.mc_var = self.mc_branch - self.mc_factory

    fm_var  = fields.Float(compute = '_compute_fm')

    # fm_var field temporarily stores variance between FM at buying station and destination WH, 
    # function compute to compute varianice and return to FM_var
    @api.depends('fm_branch', 'fm_factory')
    def _compute_fm(self):
        self.fm_var = self.fm_branch - self.fm_factory

    
    # black_var field temporarily stores variance between Black at buying station and destination WH, 
    # function compute to compute varianice and return to Black_var
    black_var  = fields.Float(compute = '_compute_black')
    @api.depends('black_branch', 'black_factory')
    def _compute_black(self):
        self.black_var = self.black_branch - self.black_factory


    # broken_var field temporarily stores variance between Broken at buying station and destination WH, 
    # function compute to compute varianice and return to broken_var
    broken_var  = fields.Float(compute = '_compute_broken')
    @api.depends('broken_branch', 'broken_factory')
    def _compute_broken(self):
        self.broken_var = self.broken_branch - self.broken_factory

    # brown_var field temporarily stores variance between Brown at buying station and destination WH, 
    # function compute to compute varianice and return to brown_var
    brown_var  = fields.Float(compute = '_compute_brown')
    @api.depends('brown_branch', 'brown_factory')
    def _compute_brown(self):
        self.brown_var = self.brown_branch - self.brown_factory

    mold_var  = fields.Float(compute = '_compute_mold')
    @api.depends('mold_branch', 'mold_factory')
    def _compute_mold(self):
        self.mold_var = self.mold_branch - self.mold_factory

    # cherry_var field temporarily stores variance between Cherry at buying station and destination WH, 
    # function compute to compute varianice and return to cherry_var
    cherry_var  = fields.Float(compute = '_compute_cherry')
    @api.depends('cherry_branch', 'cherry_factory')
    def _compute_cherry(self):
        self.cherry_var = self.cherry_branch - self.cherry_factory

    excelsa_var  = fields.Float(compute = '_compute_excelsa')
    @api.depends('excelsa_branch', 'excelsa_factory')
    def _compute_excelsa(self):
        self.excelsa_var = self.excelsa_branch - self.excelsa_factory

    screen20_var  = fields.Float(compute = '_compute_scr20')
    @api.depends('screen20_branch', 'screen20_factory')
    def _compute_scr20(self):
        self.screen20_var = self.screen20_branch - self.screen20_factory

    screen19_var  = fields.Float(compute = '_compute_scr19')
    @api.depends('screen19_branch', 'screen19_factory')
    def _compute_scr19(self):
        self.screen19_var = self.screen19_branch - self.screen19_factory

    # screen18_var field temporarily stores variance between Screen 18 at buying station and destination WH, 
    # function compute to compute varianice and return to screen18_var
    screen18_var  = fields.Float(compute = '_compute_scr18')
    @api.depends('screen18_branch', 'screen18_factory')
    def _compute_scr18(self):
        self.screen18_var = self.screen18_branch - self.screen18_factory

    # screen16_var field temporarily stores variance between Screen 16 at buying station and destination WH, 
    # function compute to compute varianice and return to screen16_var
    screen16_var  = fields.Float(compute = '_compute_scr16')
    @api.depends('screen16_branch', 'screen16_factory')
    def _compute_scr16(self):
        self.screen16_var = self.screen16_branch - self.screen16_factory

    # screen13_var field temporarily stores variance between Screen 13 at buying station and destination WH, 
    # function compute to compute varianice and return to screen13_var
    screen13_var  = fields.Float(compute = '_compute_scr13')
    @api.depends('screen13_factory', 'screen13_factory')
    def _compute_scr13(self):
        self.screen13_var = self.screen13_factory - self.screen13_factory

    # belowscr12_var field temporarily stores variance between BL-12 at buying station and destination WH, 
    # function compute to compute varianice and return to belowscr12_var
    belowscr12_var  = fields.Float(compute = '_compute_belowscr12')
    @api.depends('belowsc12_branch', 'belowsc12_factory')
    def _compute_belowscr12(self):
        self.belowscr12_var = self.belowsc12_branch - self.belowsc12_factory
    
    burned_var  = fields.Float(compute = '_compute_burned')
    @api.depends('burned_branch', 'burned_factory')
    def _compute_burned(self):
        self.burned_var = self.burned_branch - self.burned_factory

    eaten_var  = fields.Float(compute = '_compute_eaten')
    @api.depends('eaten_branch', 'eaten_factory')
    def _compute_eaten(self):
        self.eaten_var = self.eaten_branch - self.eaten_factory

    immature_var  = fields.Float(compute = '_compute_immature')
    @api.depends('immature_branch', 'immature_factory')
    def _compute_immature(self):
        self.immature_var = self.immature_branch - self.immature_factory


    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'v_grn_matching')
        self.env.cr.execute(""" 
            CREATE OR REPLACE VIEW v_grn_matching AS 
            Select row_number() OVER (
                ORDER BY (
                    b.date_done,
                    f.date_done,
                    b.description_name,
                    b.shortname,
                    b.truck_com,
                    f.backorder_id,
                    f.name,
                    b.deduction_branch,
                    f.deduction_factory,
                    b.product,
                    b.inspector
                ) DESC  
            
                ) AS id, b.id AS branch_id,
                b.description_name AS grn_branch,
                b.shortname,
                b.truck_com,
                b.date_done AS branch_date_received,
                f.backorder_id,
                f.name AS grn_factory,
                f.date_done AS factory_date_received,
                b.deduction_branch,
                f.deduction_factory,
                b.deduction_branch - f.deduction_factory AS brn_fac,
                    CASE
                        WHEN (b.deduction_branch - f.deduction_factory) > 0.2 THEN 'Deficit'::text
                        ELSE ''::text
                    END AS deficit,
                b.product,
                b.inspector as x_inspectator,
                b.product_qty AS net_weight_branch,
                f.product_qty AS net_weight_factory,
                b.product_qty - f.product_qty AS net_weight_deficit,
                b.basis_weight AS basis_weight_branch,
                f.basis_weight AS basis_weight_factory,
                b.basis_weight - f.basis_weight AS basis_weight_deficit,
                b.mc AS mc_branch,
                f.mc AS mc_factory,
                b.fm AS fm_branch,
                f.fm AS fm_factory,
                b.black AS black_branch,
                f.black AS black_factory,
                b.broken AS broken_branch,
                f.broken AS broken_factory,
                b.brown AS brown_branch,
                f.brown AS brown_factory,
                b.cherry AS cherry_branch,
                f.cherry AS cherry_factory,
                b.screen20 AS screen20_branch,
                f.screen20 AS screen20_factory,
                b.screen19 AS screen19_branch,
                f.screen19 AS screen19_factory,
                b.screen18 AS screen18_branch,
                f.screen18 AS screen18_factory,
                b.screen16 AS screen16_branch,
                f.screen16 AS screen16_factory,
                b.screen13 AS screen13_branch,
                f.screen13 AS screen13_factory,
                b.belowsc12 AS belowsc12_branch,
                f.belowsc12 AS belowsc12_factory,
                b.mold AS mold_branch,
                f.mold AS mold_factory,
                b.excelsa AS excelsa_branch,
                f.excelsa AS excelsa_factory,
                b.burned AS burned_branch,
                f.burned AS burned_factory,
                b.eaten AS eaten_branch,
                f.eaten AS eaten_factory,
                b.immature AS immature_branch,
                f.immature AS immature_factory,
                (b.product_qty - f.product_qty) /
                    CASE
                        WHEN b.product_qty > f.product_qty THEN b.product_qty
                        ELSE f.product_qty
                    END * 100::numeric AS net_var,
                (b.basis_weight - f.basis_weight) /
                    CASE
                        WHEN b.basis_weight > f.basis_weight THEN b.basis_weight
                        ELSE f.basis_weight
                    END * 100::numeric AS basis_var,
                b.vehicle_no
               FROM ( SELECT sp_b.id,
                        sp_b.description_name,
                        sp_b.date_done,
                        rpn_truck.shortname truck_com,
                        rpn.shortname,
                        pp.default_code AS product,
                        rkl_b.deduction AS deduction_branch,
                        rkl_b.product_qty,
                        rkl_b.basis_weight,
                        rkl_b.mc,
                        rkl_b.fm,
                        rkl_b.black,
                        rkl_b.broken,
                        rkl_b.brown,
                        rkl_b.mold,
                        rkl_b.cherry,
                        rkl_b.excelsa,
                        rkl_b.screen20,
                        rkl_b.screen19,
                        rkl_b.screen18,
                        rkl_b.screen16,
                        rkl_b.screen13,
                        rkl_b.belowsc12,
                        rkl_b.burned,
                        rkl_b.eaten,
                        rkl_b.immature,
                        rkl_b.inspector,
                        sp_b.vehicle_no
                       FROM stock_picking sp_b
                            JOIN stock_picking_type spt on sp_b.picking_type_id = spt.id
                            JOIN request_kcs_line rkl_b ON sp_b.id = rkl_b.picking_id
                            JOIN res_partner rpn ON sp_b.partner_id = rpn.id
                            LEFT JOIN res_partner rpn_truck ON sp_b.trucking_id = rpn_truck.id
                            JOIN product_product pp ON rkl_b.product_id = pp.id
                      WHERE spt.code::text = 'incoming'::text AND sp_b.backorder_id IS NULL AND sp_b.picking_type_id not in (199,276,240,267,231)) b
                 LEFT JOIN ( SELECT sp_f.backorder_id,
                        sp_f.name,
                        sp_f.date_done,
                        rkl_f.deduction AS deduction_factory,
                        rkl_f.product_qty,
                        rkl_f.basis_weight,
                        rkl_f.mc,
                        rkl_f.fm,
                        rkl_f.black,
                        rkl_f.broken,
                        rkl_f.brown,
                        rkl_f.mold,
                        rkl_f.cherry,
                        rkl_f.excelsa,
                        rkl_f.screen20,
                        rkl_f.screen19,
                        rkl_f.screen18,
                        rkl_f.screen16,
                        rkl_f.screen13,
                        rkl_f.belowsc12,
                        rkl_f.burned,
                        rkl_f.eaten,
                        rkl_f.immature
                       FROM stock_picking sp_f
                            JOIN stock_picking_type spt_f on sp_f.picking_type_id = spt_f.id
                            JOIN request_kcs_line rkl_f ON sp_f.id = rkl_f.picking_id
                      WHERE spt_f.code::text = 'incoming'::text) f ON b.id = f.backorder_id;
            """)
