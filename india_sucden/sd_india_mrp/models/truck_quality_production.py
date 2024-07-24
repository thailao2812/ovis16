# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict
import re

DATE_FORMAT = "%Y-%m-%d"
import datetime, time

from datetime import datetime


class TruckQualityProduction(models.Model):
    _name = "truck.quality.production"
    _inherit = ['mail.thread']

    name = fields.Char(string='Name', compute='compute_name', store=True)
    production_id = fields.Many2one('mrp.production', string='Manufacturing Order (Batch No)')
    product_id = fields.Many2one('product.product', string='Product')
    no_of_bag = fields.Float(string='Number of bag', digits=(12,0))
    quantity = fields.Float(string='Quantity (Kgs)', digits=(12,0))
    wb_slip_number = fields.Char(string='WB Slip Number')
    template_qc = fields.Selection(related='product_id.template_qc', store=True)
    truck_number = fields.Char(string='Truck Number')
    department = fields.Char(string='Department')
    department_stage = fields.Selection([
        ('qc', 'QC'),
        ('mill', 'Mill')
    ], string='Department', default=None)
    date = fields.Date(string='Date')

    sample_weight_india = fields.Float(string='Sample Weight', digits=(12, 2))

    outturn_gram = fields.Float(string='Outturn', digits=(12, 2))
    outturn_percent = fields.Float(string='Outturn%', compute='compute_outturn_percent', store=True, digits=(12, 2))

    aaa_gram = fields.Float(string="AAA", digits=(12, 2))
    aaa_percent = fields.Float(string="AAA%", compute='compute_percent_india', store=True, digits=(12, 2))

    aa_gram = fields.Float(string="AA", digits=(12, 2))
    aa_percent = fields.Float(string="AA%", compute='compute_percent_india', store=True, digits=(12, 2))

    a_gram = fields.Float(string="A", digits=(12, 2))
    a_percent = fields.Float(string="A%", compute='compute_percent_india', store=True, digits=(12, 2))

    b_gram = fields.Float(string="B", digits=(12, 2))
    b_percent = fields.Float(string="B%", compute='compute_percent_india', store=True, digits=(12, 2))

    c_gram = fields.Float(string="C", digits=(12, 2))
    c_percent = fields.Float(string="C%", compute='compute_percent_india', store=True, digits=(12, 2))

    pb_gram = fields.Float(string="PB", digits=(12, 2))
    pb_percent = fields.Float(string="PB%", compute='compute_percent_india', store=True, digits=(12, 2))

    bb_gram = fields.Float(string="BB", digits=(12, 2))
    bb_percent = fields.Float(string="BB%", compute='compute_percent_india', store=True, digits=(12, 2))

    bleached_gram = fields.Float(string="Bleached", digits=(12, 2))
    bleached_percent = fields.Float(string="Bleached%", compute='compute_percent_india', store=True, digits=(12, 2))

    idb_gram = fields.Float(string="IDB", digits=(12, 2))
    idb_percent = fields.Float(string="IDB%", compute='compute_percent_india', store=True, digits=(12, 2))

    bits_gram = fields.Float(string="Bits", digits=(12, 2))
    bits_percent = fields.Float(string="Bits%", compute='compute_percent_india', store=True, digits=(12, 2))

    hulks_gram = fields.Float(string="Husk", digits=(12, 2))
    hulks_percent = fields.Float(string="Husk%", compute='compute_percent_india', store=True, digits=(12, 2))

    stone_gram = fields.Float(string="Stone", digits=(12, 2))
    stone_percent = fields.Float(string="Stone%", compute='compute_percent_india', store=True, digits=(12, 2))

    skin_out_gram = fields.Float(string='Skin Out', digits=(12, 2))
    skin_out_percent = fields.Float(string='Skin Out%', compute='compute_percent_india', store=True, digits=(12, 2))

    triage_gram = fields.Float(string='Triage', digits=(12, 2))
    triage_percent = fields.Float(string='Triage%', compute='compute_percent_india', store=True, digits=(12, 2))

    wet_bean_gram = fields.Float(string='Wet Beans', digits=(12, 2))
    wet_bean_percent = fields.Float(string='Wet Beans%', compute='compute_percent_india', store=True, digits=(12, 2))

    red_beans_gram = fields.Float(string='Red Beans', digits=(12, 2))
    red_beans_percent = fields.Float(string='Red Beans%', compute='compute_percent_india', store=True, digits=(12, 2))

    stinker_gram = fields.Float(string='Stinker', digits=(12, 2))
    stinker_percent = fields.Float(string='Stinker%', compute='compute_percent_india', store=True, digits=(12, 2))

    faded_gram = fields.Float(string='Faded', digits=(12, 2))
    faded_percent = fields.Float(string='Faded%', compute='compute_percent_india', store=True, digits=(12, 2))

    flat_gram = fields.Float(string='Flat', digits=(12, 2))
    flat_percent = fields.Float(string='Flat%', compute='compute_percent_india', store=True, digits=(12, 2))

    pb1_gram = fields.Float(string='PB1', digits=(12, 2))
    pb1_percent = fields.Float(string='PB1%', compute='compute_percent_india', store=True, digits=(12, 2))

    pb2_gram = fields.Float(string='PB2', digits=(12, 2))
    pb2_percent = fields.Float(string='PB2%', compute='compute_percent_india', store=True, digits=(12, 2))

    sleeve_6_up = fields.Float(string='6↑', digits=(12, 2))
    sleeve_6_up_percent = fields.Float(string='6↑ %', compute='compute_percent_india', store=True, digits=(12, 2))

    sleeve_5_5_up = fields.Float(string='5.5↑', digits=(12, 2))
    sleeve_5_5_up_percent = fields.Float(string='5.5↑ %', compute='compute_percent_india', store=True, digits=(12, 2))

    sleeve_5_5_down = fields.Float(string='5.5↓', digits=(12, 2))
    sleeve_5_5_down_percent = fields.Float(string='5.5↓%', compute='compute_percent_india', store=True, digits=(12, 2))

    sleeve_5_down = fields.Float(string='5↓', digits=(12, 2))
    sleeve_5_down_percent = fields.Float(string='5↓ %', compute='compute_percent_india', store=True, digits=(12, 2))

    sleeve_5_up = fields.Float(string='5↑', digits=(12, 2))
    sleeve_5_up_percent = fields.Float(string='5↑ %', compute='compute_percent_india', store=True, digits=(12, 2))

    unhulled = fields.Float(string='Unhulled', digits=(12, 2))
    unhulled_percent = fields.Float(string='Unhulled %', compute='compute_percent_india', store=True, digits=(12, 2))

    remaining_coffee = fields.Float(string='Remaining Coffee', digits=(12, 2))
    remaining_coffee_percent = fields.Float(string='Remaining Coffee %', compute='compute_percent_india', store=True,
                                            digits=(12, 2))

    blacks = fields.Float(string='Blacks', digits=(12, 2))
    blacks_percent = fields.Float(string='Blacks %', compute='compute_percent_india', store=True, digits=(12, 2))

    half_monsoon = fields.Float(string='Half Monsoon', digits=(12, 2))
    half_monsoon_percent = fields.Float(string='Half Monsoon %', compute='compute_percent_india', store=True,
                                        digits=(12, 2))

    good_beans = fields.Float(string='Good Beans', digits=(12, 2))
    good_beans_percent = fields.Float(string='Good Beans %', compute='compute_percent_india', store=True,
                                      digits=(12, 2))

    total_gram = fields.Float(string='Total', compute='compute_percent_india', store=True)
    total_percent = fields.Float(string='Total%', compute='compute_total_percent', store=True, digits=(12, 2))

    moisture_percent = fields.Float(string='Moisture%', digits=(12, 2))

    @api.depends('outturn_gram')
    def compute_outturn_percent(self):
        for record in self:
            if record.outturn_gram:
                record.outturn_percent = (record.outturn_gram / 1000) * 100
            else:
                record.outturn_percent = 0

    @api.depends('aaa_gram', 'aa_gram', 'a_gram', 'b_gram', 'c_gram', 'pb_gram', 'bb_gram', 'bleached_gram', 'idb_gram',
                 'bits_gram', 'hulks_gram', 'stone_gram', 'template_qc', 'sleeve_6_up', 'sleeve_5_5_up',
                 'sleeve_5_5_down', 'sleeve_5_down', 'skin_out_gram', 'triage_gram', 'wet_bean_gram', 'red_beans_gram',
                 'stinker_gram', 'faded_gram', 'flat_gram', 'pb1_gram', 'pb2_gram', 'sleeve_5_up', 'unhulled',
                 'remaining_coffee', 'blacks', 'half_monsoon', 'good_beans')
    def compute_percent_india(self):
        for record in self:
            record.total_gram = 0
            if record.template_qc == 'raw':
                record.total_gram = round(record.aaa_gram + record.aa_gram + record.a_gram + record.b_gram \
                                          + record.c_gram + record.pb_gram + record.bb_gram + record.bleached_gram \
                                          + record.idb_gram + record.bits_gram + record.hulks_gram + record.stone_gram \
                                          + record.skin_out_gram + record.triage_gram + record.wet_bean_gram \
                                          + record.red_beans_gram + record.stinker_gram + record.faded_gram, 2)
            if record.template_qc == 'clean':
                record.total_gram = round(record.aaa_gram + record.aa_gram + record.a_gram + record.b_gram \
                                          + record.c_gram, 2)
            if record.template_qc == 'c_grade':
                record.total_gram = round(record.sleeve_6_up + record.sleeve_5_5_down + record.sleeve_5_down + \
                                          record.sleeve_5_5_up, 2)
            if record.template_qc == 'pb_grade':
                record.total_gram = round(record.flat_gram + record.pb1_gram + record.pb2_gram, 2)
            if record.template_qc == 'bulk':
                record.total_gram = round(record.aaa_gram + record.aa_gram + record.a_gram + record.b_gram \
                                    + record.c_gram + record.pb_gram + record.bb_gram + record.bleached_gram \
                                    + record.idb_gram + record.bits_gram + record.hulks_gram + record.stone_gram \
                                    + record.skin_out_gram + record.triage_gram + record.wet_bean_gram \
                                    + record.red_beans_gram + record.stinker_gram + record.faded_gram + record.unhulled ,2)
            if record.total_gram > 0:
                record.aaa_percent = record.aaa_gram / record.total_gram * 100
                record.aa_percent = record.aa_gram / record.total_gram * 100
                record.a_percent = record.a_gram / record.total_gram * 100
                record.b_percent = record.b_gram / record.total_gram * 100
                record.c_percent = record.c_gram / record.total_gram * 100
                record.pb_percent = record.pb_gram / record.total_gram * 100
                record.bb_percent = record.bb_gram / record.total_gram * 100
                record.bleached_percent = record.bleached_gram / record.total_gram * 100
                record.idb_percent = record.idb_gram / record.total_gram * 100
                record.bits_percent = record.bits_gram / record.total_gram * 100
                record.hulks_percent = record.hulks_gram / record.total_gram * 100
                record.stone_percent = record.stone_gram / record.total_gram * 100
                record.skin_out_percent = record.skin_out_gram / record.total_gram * 100
                record.triage_percent = record.triage_gram / record.total_gram * 100
                record.wet_bean_percent = record.wet_bean_gram / record.total_gram * 100
                record.red_beans_percent = record.red_beans_gram / record.total_gram * 100
                record.stinker_percent = record.stinker_gram / record.total_gram * 100
                record.faded_percent = record.faded_gram / record.total_gram * 100
                record.flat_percent = record.flat_gram / record.total_gram * 100
                record.pb1_percent = record.pb1_gram / record.total_gram * 100
                record.pb2_percent = record.pb2_gram / record.total_gram * 100
                record.sleeve_6_up_percent = record.sleeve_6_up / record.total_gram * 100
                record.sleeve_5_5_up_percent = record.sleeve_5_5_up / record.total_gram * 100
                record.sleeve_5_5_down_percent = record.sleeve_5_5_down / record.total_gram * 100
                record.sleeve_5_down_percent = record.sleeve_5_down / record.total_gram * 100

                record.sleeve_5_up_percent = record.sleeve_5_up / record.total_gram * 100
                record.unhulled_percent = record.unhulled / record.total_gram * 100
                record.remaining_coffee_percent = record.remaining_coffee / record.total_gram * 100
                record.blacks_percent = record.blacks / record.total_gram * 100
                record.half_monsoon_percent = record.half_monsoon / record.total_gram * 100
                record.good_beans_percent = record.good_beans / record.total_gram * 100

    @api.depends('outturn_percent', 'aaa_percent', 'aa_percent', 'a_percent', 'b_percent', 'c_percent', 'pb_percent',
                 'bb_percent', 'bleached_percent', 'idb_percent', 'bits_percent', 'hulks_percent', 'stone_percent',
                 'skin_out_percent', 'triage_percent', 'wet_bean_percent', 'red_beans_percent', 'stinker_percent',
                 'faded_percent', 'flat_percent', 'pb1_percent', 'pb2_percent', 'sleeve_6_up_percent',
                 'sleeve_5_5_up_percent', 'sleeve_5_5_down_percent', 'sleeve_5_down_percent', 'template_qc',
                 'total_gram',
                 'sleeve_5_up_percent', 'unhulled_percent', 'remaining_coffee_percent', 'blacks_percent',
                 'half_monsoon_percent', 'good_beans_percent')
    def compute_total_percent(self):
        for record in self:
            record.total_percent = 0
            if record.template_qc == 'raw':
                record.total_percent = record.aaa_percent + record.aa_percent + record.a_percent \
                                       + record.b_percent + record.c_percent + record.pb_percent + record.bb_percent \
                                       + record.bleached_percent + record.idb_percent + record.bits_percent \
                                       + record.hulks_percent + record.stone_percent + record.skin_out_percent \
                                       + record.triage_percent + record.wet_bean_percent + record.red_beans_percent \
                                       + record.stinker_percent + record.faded_percent
            if record.template_qc == 'bulk':
                record.total_percent = record.aaa_percent + record.aa_percent + record.a_percent \
                                       + record.b_percent + record.c_percent + record.pb_percent + record.bb_percent \
                                       + record.bleached_percent + record.idb_percent + record.bits_percent \
                                       + record.hulks_percent + record.stone_percent + record.skin_out_percent \
                                       + record.triage_percent + record.wet_bean_percent + record.red_beans_percent \
                                       + record.stinker_percent + record.faded_percent + record.unhulled_percent
            if record.template_qc == 'clean':
                record.total_percent = record.aaa_percent + record.aa_percent + record.a_percent \
                                       + record.b_percent + record.c_percent
            if record.template_qc == 'c_grade':
                record.total_percent = record.sleeve_6_up_percent + record.sleeve_5_5_up_percent \
                                       + record.sleeve_5_5_down_percent + record.sleeve_5_down_percent
            if record.template_qc == 'pb_grade':
                record.total_percent = record.flat_percent + record.pb1_percent + record.pb2_percent
            if record.total_gram == 300:
                record.total_percent = 100


    @api.depends('truck_number')
    def compute_name(self):
        for rec in self:
            if rec.truck_number:
                rec.name = 'Quality Checking for Truck: %s' % rec.truck_number
            else:
                rec.name = 'Quality Checking for Truck'


