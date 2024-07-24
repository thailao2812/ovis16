# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError

class RequestKCSLine(models.Model):
    _inherit = 'request.kcs.line'

    state = fields.Selection(selection=[('draft', 'New'), ('commercial', 'Commercial'), ('approved', 'Approved'), ('reject', 'Reject')],
                             string='Status', readonly=True, copy=False,
                             index=True, default='draft', )

    template_qc = fields.Selection(related='product_id.template_qc', store=True)
    visual_quality_ids = fields.Many2many('visual.quality',
                                          string='Visual Quality')

    sample_weight_india = fields.Float(string='Sample Weight (Gr)', digits=(12, 2))

    outturn_gram = fields.Float(string='Outturn', digits=(12, 2))
    outturn_percent = fields.Float(string='Outturn%', compute='compute_outturn_percent', store=True, digits=(12, 2))

    aaa_gram = fields.Float(string="AAA", digits=(12, 2))
    aaa_percent = fields.Float(string="AAA%", compute='compute_percent_india', store=True)

    aa_gram = fields.Float(string="AA", digits=(12, 2))
    aa_percent = fields.Float(string="AA%", compute='compute_percent_india', store=True)

    a_gram = fields.Float(string="A", digits=(12, 2))
    a_percent = fields.Float(string="A%", compute='compute_percent_india', store=True)

    b_gram = fields.Float(string="B", digits=(12, 2))
    b_percent = fields.Float(string="B%", compute='compute_percent_india', store=True)

    c_gram = fields.Float(string="C", digits=(12, 2))
    c_percent = fields.Float(string="C%", compute='compute_percent_india', store=True)

    pb_gram = fields.Float(string="PB", digits=(12, 2))
    pb_percent = fields.Float(string="PB%", compute='compute_percent_india', store=True)

    bb_gram = fields.Float(string="BB", digits=(12, 2))
    bb_percent = fields.Float(string="BB%", compute='compute_percent_india', store=True)

    bleached_gram = fields.Float(string="Bleached", digits=(12, 2))
    bleached_percent = fields.Float(string="Bleached%", compute='compute_percent_india', store=True)

    idb_gram = fields.Float(string="IDB", digits=(12, 2))
    idb_percent = fields.Float(string="IDB%", compute='compute_percent_india', store=True)

    bits_gram = fields.Float(string="Bits", digits=(12, 2))
    bits_percent = fields.Float(string="Bits%", compute='compute_percent_india', store=True)

    hulks_gram = fields.Float(string="Husk", digits=(12, 2))
    hulks_percent = fields.Float(string="Husk%", compute='compute_percent_india', store=True)

    stone_gram = fields.Float(string="Stone", digits=(12, 2))
    stone_percent = fields.Float(string="Stone%", compute='compute_percent_india', store=True)

    skin_out_gram = fields.Float(string='Skin Out', digits=(12, 2))
    skin_out_percent = fields.Float(string='Skin Out%', compute='compute_percent_india', store=True)

    triage_gram = fields.Float(string='Triage', digits=(12, 2))
    triage_percent = fields.Float(string='Triage%', compute='compute_percent_india', store=True)

    wet_bean_gram = fields.Float(string='Wet Beans', digits=(12, 2))
    wet_bean_percent = fields.Float(string='Wet Beans%', compute='compute_percent_india', store=True)

    red_beans_gram = fields.Float(string='Red Beans', digits=(12, 2))
    red_beans_percent = fields.Float(string='Red Beans%', compute='compute_percent_india', store=True)

    stinker_gram = fields.Float(string='Stinker', digits=(12, 2))
    stinker_percent = fields.Float(string='Stinker%', compute='compute_percent_india', store=True)

    faded_gram = fields.Float(string='Faded', digits=(12, 2))
    faded_percent = fields.Float(string='Faded%', compute='compute_percent_india', store=True)

    flat_gram = fields.Float(string='Flat', digits=(12, 2))
    flat_percent = fields.Float(string='Flat%', compute='compute_percent_india', store=True)

    pb1_gram = fields.Float(string='PB1', digits=(12, 2))
    pb1_percent = fields.Float(string='PB1%', compute='compute_percent_india', store=True)

    pb2_gram = fields.Float(string='PB2', digits=(12, 2))
    pb2_percent = fields.Float(string='PB2%', compute='compute_percent_india', store=True)

    sleeve_6_up = fields.Float(string='6↑', digits=(12, 2))
    sleeve_6_up_percent = fields.Float(string='6↑ %', compute='compute_percent_india', store=True)

    sleeve_5_5_up = fields.Float(string='5.5↑', digits=(12, 2))
    sleeve_5_5_up_percent = fields.Float(string='5.5↑ %', compute='compute_percent_india', store=True)

    sleeve_5_5_down = fields.Float(string='5.5↓', digits=(12, 2))
    sleeve_5_5_down_percent = fields.Float(string='5.5↓%', compute='compute_percent_india', store=True)

    sleeve_5_down = fields.Float(string='5↓', digits=(12, 2))
    sleeve_5_down_percent = fields.Float(string='5↓ %', compute='compute_percent_india', store=True)

    sleeve_5_up = fields.Float(string='5↑', digits=(12, 2))
    sleeve_5_up_percent = fields.Float(string='5↑ %', compute='compute_percent_india', store=True, digits=(12, 2))

    unhulled = fields.Float(string='Unhulled', digits=(12, 2))
    unhulled_percent = fields.Float(string='Unhulled %', compute='compute_percent_india', store=True, digits=(12, 2))

    remaining_coffee = fields.Float(string='Remaining Coffee', digits=(12, 2))
    remaining_coffee_percent = fields.Float(string='Remaining Coffee %', compute='compute_percent_india', store=True, digits=(12, 2))

    blacks = fields.Float(string='Blacks', digits=(12, 2))
    blacks_percent = fields.Float(string='Blacks %', compute='compute_percent_india', store=True, digits=(12, 2))

    half_monsoon = fields.Float(string='Half Monsoon', digits=(12, 2))
    half_monsoon_percent = fields.Float(string='Half Monsoon %', compute='compute_percent_india', store=True, digits=(12, 2))

    good_beans = fields.Float(string='Good Beans', digits=(12, 2))
    good_beans_percent = fields.Float(string='Good Beans %', compute='compute_percent_india', store=True, digits=(12, 2))

    total_gram = fields.Float(string='Total', compute='compute_percent_india', store=True)
    total_percent = fields.Float(string='Total%', compute='compute_total_percent', store=True)

    moisture_percent = fields.Float(string='Moisture%', digits=(12, 2), compute='_compute_moisture_percent', store=True)

    # Deduction O2m
    deduction_ids = fields.One2many('deduction.line', 'request_kcs_line_id', string='Deduction Line')
    deduction_special_ids = fields.One2many('deduction.line', 'request_kcs_line_id_2nd', string='Deduction Line')
    # Deduction
    moisture_deduct = fields.Float(string='Moisture Deduction %', digits=(12, 2))
    moisture_deduct_kg = fields.Float(string='Moisture Deduction Kg', digits=(12, 2))
    moisture_deduct_entry = fields.Float(string='Moisture Deduction Commercial', digits=(12, 2))
    remark_moisture = fields.Char(string='Remark Moisture Deduction')

    outturn_deduct = fields.Float(string='Outturn Deduction %', digits=(12, 2))
    outturn_deduct_kg = fields.Float(string='Outturn Deduction Kg', digits=(12, 2))
    outturn_deduct_entry = fields.Float(string='Outturn Deduction Commercial', digits=(12, 2))
    remark_outturn = fields.Char(string='Remark Outturn Deduction')

    a_ab_grade_deduct = fields.Float(string='A/AB Grade Deduction %', digits=(12, 2))
    a_ab_grade_deduct_kg = fields.Float(string='A/AB Grade Deduction Kg', digits=(12, 2))
    a_ab_grade_deduct_entry = fields.Float(string='A/AB Grade Deduction Commercial', digits=(12, 2))
    remark_a_ab_grade = fields.Char(string='Remark Grade Deduction')

    bb_bleach_idb_deduct = fields.Float(string='BB/Bleached/IDB Deduction %', digits=(12, 2))
    bb_bleach_idb_deduct_kg = fields.Float(string='BB/Bleached/IDB Deduction Kg', digits=(12, 2))
    bb_bleach_idb_deduct_entry = fields.Float(string='BB/Bleached/IDB Deduction Commercial', digits=(12, 2))
    remark_bb_bleach_idb = fields.Char(string='Remark Bleach Deduction')

    hulks_stone_deduct = fields.Float(string='Husk / Stone Deduction %', digits=(12, 2))
    hulks_stone_deduct_kg = fields.Float(string='Husk / Stone Deduction Kg', digits=(12, 2))
    hulks_stone_deduct_entry = fields.Float(string='Husk / Stone Deduction Commercial', digits=(12, 2))
    remark_hulks_stone = fields.Char(string='Remark Husk/Stone Deduction')

    skinout_deduct = fields.Float(string='Skinout Deduction %', digits=(12, 2))
    skinout_deduct_kg = fields.Float(string='Skinout Deduction Kg', digits=(12, 2))
    skinout_deduct_entry = fields.Float(string='Skinout Deduction Commercial', digits=(12, 2))
    remark_skinout = fields.Char(string='Remark Skinout Deduction')

    other_dying_deduct = fields.Float(string='Other / Drying Deduction %', digits=(12, 2))
    other_dying_deduct_kg = fields.Float(string='Other / Drying Deduction Kg', digits=(12, 2))
    other_dying_deduct_entry = fields.Float(string='Other / Drying Deduction Commercial', digits=(12, 2))
    remark_other_dying = fields.Char(string='Remark Other Deduction')

    criterions_id = fields.Many2one(related='picking_id.kcs_criterions_id', string="KCS Criterion", readonly=True,
                                    states={'draft': [('readonly', False)]}, store=True)

    qty_reached = fields.Float(compute='_compute_deduction_weight_india', string="Deduction Weight", store=True, digits=(12, 0))
    basis_weight = fields.Float(compute='_compute_deduction_weight_india', string="Basis Weight", store=True, digits=(12, 0))

    #new deduction
    moisture_deduct_commercial = fields.Float(string='Moisture Deduction Commercial Dept', compute='compute_data_new_deduction', store=True)
    outturn_deduct_commercial = fields.Float(string='Outturn Deduction Commercial Dept', compute='compute_data_new_deduction', store=True)
    a_ab_grade_deduct_commercial = fields.Float(string='A/AB Grade Deduction Commercial Dept', compute='compute_data_new_deduction', store=True)
    pb_deduct_commercial = fields.Float(string='PB Deduction Commercial Dept', compute='compute_data_new_deduction', store=True)
    husk_deduct_commercial = fields.Float(string='Husk Deduction Commercial Dept', compute='compute_data_new_deduction', store=True)
    stone_deduct_commercial = fields.Float(string='Stone Deduction Commercial Dept', compute='compute_data_new_deduction', store=True)
    skin_out_deduct_commercial = fields.Float(string='Skin Out Deduction Commercial Dept', compute='compute_data_new_deduction', store=True)
    drying_deduct_commercial = fields.Float(string='Drying Deduction Commercial Dept', compute='compute_data_new_deduction', store=True)
    stinker_deduct_commercial = fields.Float(string='Stinker Deduction Commercial Dept', compute='compute_data_new_deduction', store=True)
    dust_deduct_commercial = fields.Float(string='Dust Deduction Commercial Dept', compute='compute_data_new_deduction', store=True)
    faded_deduct_commercial = fields.Float(string='Faded Deduction Commercial Dept', compute='compute_data_new_deduction', store=True)
    triage_deduct_commercial = fields.Float(string='Triages Deduction Commercial Dept', compute='compute_data_new_deduction', store=True)
    jut_black_deduct_commercial = fields.Float(string='Jut Black Deduction Commercial Dept', compute='compute_data_new_deduction', store=True)
    unhauled_deduct_commercial = fields.Float(string='Unhauled Deduction Commercial Dept', compute='compute_data_new_deduction', store=True)
    wet_bean_deduct_commercial = fields.Float(string='Wet Bean Deduction Commercial Dept', compute='compute_data_new_deduction', store=True)
    special_deduct_commercial = fields.Float(string='BB/Bleached/IDB/Red Beans Deduction Commercial Dept', compute='compute_data_new_deduction', store=True)

    moisture_deduct_qc = fields.Float(string='Moisture Deduction QC', compute='compute_data_new_deduction', store=True)
    outturn_deduct_qc= fields.Float(string='Outturn Deduction QC', compute='compute_data_new_deduction', store=True)
    a_ab_grade_deduct_qc = fields.Float(string='A/AB Grade Deduction QC', compute='compute_data_new_deduction', store=True)
    pb_deduct_qc = fields.Float(string='PB Deduction QC', compute='compute_data_new_deduction', store=True)
    husk_deduct_qc = fields.Float(string='Husk Deduction QC', compute='compute_data_new_deduction', store=True)
    stone_deduct_qc = fields.Float(string='Stone Deduction QC', compute='compute_data_new_deduction', store=True)
    skin_out_deduct_qc = fields.Float(string='Skin Out Deduction QC', compute='compute_data_new_deduction', store=True)
    drying_deduct_qc = fields.Float(string='Drying Deduction QC', compute='compute_data_new_deduction', store=True)
    stinker_deduct_qc = fields.Float(string='Stinker Deduction QC', compute='compute_data_new_deduction', store=True)
    dust_deduct_qc = fields.Float(string='Dust Deduction QC', compute='compute_data_new_deduction', store=True)
    faded_deduct_qc = fields.Float(string='Faded Deduction QC', compute='compute_data_new_deduction', store=True)
    triage_deduct_qc = fields.Float(string='Triages Deduction QC', compute='compute_data_new_deduction', store=True)
    jut_black_deduct_qc = fields.Float(string='Jut Black Deduction QC', compute='compute_data_new_deduction', store=True)
    unhauled_deduct_qc = fields.Float(string='Unhauled Deduction QC', compute='compute_data_new_deduction', store=True)
    wet_bean_deduct_qc = fields.Float(string='Wet Bean Deduction QC', compute='compute_data_new_deduction', store=True)
    special_deduct_qc = fields.Float(string='BB/Bleached/IDB/Red Beans Deduction QC', compute='compute_data_new_deduction', store=True)

    moisture_deduct_per = fields.Float(string='Moisture % QC', compute='compute_data_new_deduction', store=True)
    outturn_deduct_per = fields.Float(string='Outturn % QC', compute='compute_data_new_deduction', store=True)
    a_ab_grade_deduct_per = fields.Float(string='A/AB Grade % QC', compute='compute_data_new_deduction', store=True)
    pb_deduct_per = fields.Float(string='PB % QC', compute='compute_data_new_deduction', store=True)
    husk_deduct_per = fields.Float(string='Husk % QC', compute='compute_data_new_deduction', store=True)
    stone_deduct_per = fields.Float(string='Stone % QC', compute='compute_data_new_deduction', store=True)
    skin_out_deduct_per = fields.Float(string='Skin Out % QC', compute='compute_data_new_deduction', store=True)
    drying_deduct_per = fields.Float(string='Drying % QC', compute='compute_data_new_deduction', store=True)
    stinker_deduct_per = fields.Float(string='Stinker % QC', compute='compute_data_new_deduction', store=True)
    dust_deduct_per = fields.Float(string='Dust % QC', compute='compute_data_new_deduction', store=True)
    faded_deduct_per = fields.Float(string='Faded % QC', compute='compute_data_new_deduction', store=True)
    triage_deduct_per = fields.Float(string='Triages % QC', compute='compute_data_new_deduction', store=True)
    jut_black_deduct_per = fields.Float(string='Jut Black % QC', compute='compute_data_new_deduction', store=True)
    unhauled_deduct_per = fields.Float(string='Unhauled % QC', compute='compute_data_new_deduction', store=True)
    wet_bean_deduct_per = fields.Float(string='Wet Bean % QC', compute='compute_data_new_deduction', store=True)
    special_deduct_per = fields.Float(string='BB/Bleached/IDB/Red Beans % QC', compute='compute_data_new_deduction', store=True)
    #
    moisture_deduct_remark = fields.Text(string='Moisture Remark', compute='compute_data_new_deduction', store=True)
    outturn_deduct_remark = fields.Text(string='Outturn Remark', compute='compute_data_new_deduction', store=True)
    a_ab_grade_deduct_remark = fields.Text(string='A/AB Grade Remark', compute='compute_data_new_deduction', store=True)
    pb_deduct_remark = fields.Text(string='PB Remark', compute='compute_data_new_deduction', store=True)
    husk_deduct_remark = fields.Text(string='Husk Remark', compute='compute_data_new_deduction', store=True)
    stone_deduct_remark = fields.Text(string='Stone Remark', compute='compute_data_new_deduction', store=True)
    skin_out_deduct_remark = fields.Text(string='Skin Out Remark', compute='compute_data_new_deduction', store=True)
    drying_deduct_remark = fields.Text(string='Drying Remark', compute='compute_data_new_deduction', store=True)
    stinker_deduct_remark = fields.Text(string='Stinker Remark', compute='compute_data_new_deduction', store=True)
    dust_deduct_remark = fields.Text(string='Dust Remark', compute='compute_data_new_deduction', store=True)
    faded_deduct_remark = fields.Text(string='Faded Remark', compute='compute_data_new_deduction', store=True)
    triage_deduct_remark = fields.Text(string='Triages Remark', compute='compute_data_new_deduction', store=True)
    jut_black_deduct_remark = fields.Text(string='Jut Black Remark', compute='compute_data_new_deduction', store=True)
    unhauled_deduct_remark = fields.Text(string='Unhauled Remark', compute='compute_data_new_deduction', store=True)
    wet_bean_deduct_remark = fields.Text(string='Wet Bean Remark', compute='compute_data_new_deduction', store=True)
    special_deduct_remark = fields.Text(string='BB/Bleached/IDB/Red Beans Remark', compute='compute_data_new_deduction',store=True)

    @api.depends('deduction_ids', 'deduction_ids.commercial_input', 'deduction_ids.kg', 'deduction_ids.percent', 'deduction_ids.remark',
                 'deduction_special_ids', 'deduction_special_ids.commercial_input', 'deduction_special_ids.kg', 'deduction_special_ids.percent', 'deduction_special_ids.remark')
    def compute_data_new_deduction(self):
        for rec in self:
            if rec.deduction_ids:
                rec.moisture_deduct_commercial = rec.deduction_ids.filtered(lambda x: x.name.code == 'MD').commercial_input
                rec.outturn_deduct_commercial = rec.deduction_ids.filtered(lambda x: x.name.code == 'OD').commercial_input
                rec.a_ab_grade_deduct_commercial = rec.deduction_ids.filtered(lambda x: x.name.code == 'GD').commercial_input
                rec.pb_deduct_commercial = rec.deduction_ids.filtered(lambda x: x.name.code == 'PB').commercial_input
                rec.husk_deduct_commercial = rec.deduction_ids.filtered(lambda x: x.name.code == 'HUSK').commercial_input
                rec.stone_deduct_commercial = rec.deduction_ids.filtered(lambda x: x.name.code == 'STONE').commercial_input
                rec.skin_out_deduct_commercial = rec.deduction_ids.filtered(lambda x: x.name.code == 'SD').commercial_input
                rec.drying_deduct_commercial = rec.deduction_ids.filtered(lambda x: x.name.code == 'DRY').commercial_input
                rec.stinker_deduct_commercial = rec.deduction_ids.filtered(lambda x: x.name.code == 'STIN').commercial_input
                rec.dust_deduct_commercial = rec.deduction_ids.filtered(lambda x: x.name.code == 'DUST').commercial_input
                rec.faded_deduct_commercial = rec.deduction_ids.filtered(lambda x: x.name.code == 'FADE').commercial_input
                rec.triage_deduct_commercial = rec.deduction_ids.filtered(lambda x: x.name.code == 'TRIAGE').commercial_input
                rec.jut_black_deduct_commercial = rec.deduction_ids.filtered(lambda x: x.name.code == 'JB').commercial_input
                rec.unhauled_deduct_commercial = rec.deduction_ids.filtered(lambda x: x.name.code == 'UNHAU').commercial_input

                rec.moisture_deduct_qc = rec.deduction_ids.filtered(lambda x: x.name.code == 'MD').kg
                rec.outturn_deduct_qc = rec.deduction_ids.filtered(lambda x: x.name.code == 'OD').kg
                rec.a_ab_grade_deduct_qc = rec.deduction_ids.filtered(lambda x: x.name.code == 'GD').kg
                rec.pb_deduct_qc = rec.deduction_ids.filtered(lambda x: x.name.code == 'PB').kg
                rec.husk_deduct_qc = rec.deduction_ids.filtered(lambda x: x.name.code == 'HUSK').kg
                rec.stone_deduct_qc = rec.deduction_ids.filtered(lambda x: x.name.code == 'STONE').kg
                rec.skin_out_deduct_qc = rec.deduction_ids.filtered(lambda x: x.name.code == 'SD').kg
                rec.drying_deduct_qc = rec.deduction_ids.filtered(lambda x: x.name.code == 'DRY').kg
                rec.stinker_deduct_qc = rec.deduction_ids.filtered(lambda x: x.name.code == 'STIN').kg
                rec.dust_deduct_qc = rec.deduction_ids.filtered(lambda x: x.name.code == 'DUST').kg
                rec.faded_deduct_qc = rec.deduction_ids.filtered(lambda x: x.name.code == 'FADE').kg
                rec.triage_deduct_qc = rec.deduction_ids.filtered(lambda x: x.name.code == 'TRIAGE').kg
                rec.jut_black_deduct_qc = rec.deduction_ids.filtered(lambda x: x.name.code == 'JB').kg
                rec.unhauled_deduct_qc = rec.deduction_ids.filtered(lambda x: x.name.code == 'UNHAU').kg

                rec.moisture_deduct_per = rec.deduction_ids.filtered(lambda x: x.name.code == 'MD').percent
                rec.outturn_deduct_per = rec.deduction_ids.filtered(lambda x: x.name.code == 'OD').percent
                rec.a_ab_grade_deduct_per = rec.deduction_ids.filtered(lambda x: x.name.code == 'GD').percent
                rec.pb_deduct_per = rec.deduction_ids.filtered(lambda x: x.name.code == 'PB').percent
                rec.husk_deduct_per = rec.deduction_ids.filtered(lambda x: x.name.code == 'HUSK').percent
                rec.stone_deduct_per = rec.deduction_ids.filtered(lambda x: x.name.code == 'STONE').percent
                rec.skin_out_deduct_per = rec.deduction_ids.filtered(lambda x: x.name.code == 'SD').percent
                rec.drying_deduct_per = rec.deduction_ids.filtered(lambda x: x.name.code == 'DRY').percent
                rec.stinker_deduct_per = rec.deduction_ids.filtered(lambda x: x.name.code == 'STIN').percent
                rec.dust_deduct_per = rec.deduction_ids.filtered(lambda x: x.name.code == 'DUST').percent
                rec.faded_deduct_per = rec.deduction_ids.filtered(lambda x: x.name.code == 'FADE').percent
                rec.triage_deduct_per = rec.deduction_ids.filtered(lambda x: x.name.code == 'TRIAGE').percent
                rec.jut_black_deduct_per = rec.deduction_ids.filtered(lambda x: x.name.code == 'JB').percent
                rec.unhauled_deduct_per = rec.deduction_ids.filtered(lambda x: x.name.code == 'UNHAU').percent
                #
                rec.moisture_deduct_remark = rec.deduction_ids.filtered(lambda x: x.name.code == 'MD').remark
                rec.outturn_deduct_remark = rec.deduction_ids.filtered(lambda x: x.name.code == 'OD').remark
                rec.a_ab_grade_deduct_remark = rec.deduction_ids.filtered(lambda x: x.name.code == 'GD').remark
                rec.pb_deduct_remark = rec.deduction_ids.filtered(lambda x: x.name.code == 'PB').remark
                rec.husk_deduct_remark = rec.deduction_ids.filtered(lambda x: x.name.code == 'HUSK').remark
                rec.stone_deduct_remark = rec.deduction_ids.filtered(lambda x: x.name.code == 'STONE').remark
                rec.skin_out_deduct_remark = rec.deduction_ids.filtered(lambda x: x.name.code == 'SD').remark
                rec.drying_deduct_remark = rec.deduction_ids.filtered(lambda x: x.name.code == 'DRY').remark
                rec.stinker_deduct_remark = rec.deduction_ids.filtered(lambda x: x.name.code == 'STIN').remark
                rec.dust_deduct_remark = rec.deduction_ids.filtered(lambda x: x.name.code == 'DUST').remark
                rec.faded_deduct_remark = rec.deduction_ids.filtered(lambda x: x.name.code == 'FADE').remark
                rec.triage_deduct_remark = rec.deduction_ids.filtered(lambda x: x.name.code == 'TRIAGE').remark
                rec.jut_black_deduct_remark = rec.deduction_ids.filtered(lambda x: x.name.code == 'JB').remark
                rec.unhauled_deduct_remark = rec.deduction_ids.filtered(lambda x: x.name.code == 'UNHAU').remark
            else:
                rec.moisture_deduct_commercial = 0
                rec.outturn_deduct_commercial = 0
                rec.a_ab_grade_deduct_commercial = 0
                rec.pb_deduct_commercial = 0
                rec.husk_deduct_commercial = 0
                rec.stone_deduct_commercial = 0
                rec.skin_out_deduct_commercial = 0
                rec.drying_deduct_commercial = 0
                rec.stinker_deduct_commercial = 0
                rec.dust_deduct_commercial = 0
                rec.faded_deduct_commercial = 0
                rec.triage_deduct_commercial = 0
                rec.jut_black_deduct_commercial = 0
                rec.unhauled_deduct_commercial = 0

                rec.moisture_deduct_qc = 0
                rec.outturn_deduct_qc = 0
                rec.a_ab_grade_deduct_qc = 0
                rec.pb_deduct_qc = 0
                rec.husk_deduct_qc = 0
                rec.stone_deduct_qc = 0
                rec.skin_out_deduct_qc = 0
                rec.drying_deduct_qc = 0
                rec.stinker_deduct_qc = 0
                rec.dust_deduct_qc = 0
                rec.faded_deduct_qc = 0
                rec.triage_deduct_qc = 0
                rec.jut_black_deduct_qc = 0
                rec.unhauled_deduct_qc = 0

                rec.moisture_deduct_per = 0
                rec.outturn_deduct_per = 0
                rec.a_ab_grade_deduct_per = 0
                rec.pb_deduct_per = 0
                rec.husk_deduct_per = 0
                rec.stone_deduct_per = 0
                rec.skin_out_deduct_per = 0
                rec.drying_deduct_per = 0
                rec.stinker_deduct_per = 0
                rec.dust_deduct_per = 0
                rec.faded_deduct_per = 0
                rec.triage_deduct_per = 0
                rec.jut_black_deduct_per = 0
                rec.unhauled_deduct_per = 0
            if rec.deduction_special_ids:
                rec.wet_bean_deduct_commercial = rec.deduction_special_ids.filtered(lambda x: x.name.code == 'WB').commercial_input
                rec.wet_bean_deduct_qc = rec.deduction_special_ids.filtered(lambda x: x.name.code == 'WB').kg
                rec.wet_bean_deduct_per = rec.deduction_special_ids.filtered(lambda x: x.name.code == 'WB').percent
                rec.wet_bean_deduct_remark = rec.deduction_special_ids.filtered(lambda x: x.name.code == 'WB').remark

                rec.special_deduct_commercial = rec.deduction_special_ids.filtered(lambda x: x.name.code == '4_kinds_deduction').commercial_input
                rec.special_deduct_qc = rec.deduction_special_ids.filtered(lambda x: x.name.code == '4_kinds_deduction').kg
                rec.special_deduct_per = rec.deduction_special_ids.filtered(lambda x: x.name.code == '4_kinds_deduction').percent
                rec.special_deduct_remark = rec.deduction_special_ids.filtered(lambda x: x.name.code == '4_kinds_deduction').remark
            else:
                rec.wet_bean_deduct_commercial = 0
                rec.wet_bean_deduct_qc = 0
                rec.wet_bean_deduct_per = 0

                rec.special_deduct_commercial = 0
                rec.special_deduct_qc = 0
                rec.special_deduct_per = 0

    @api.depends('deduction_ids', 'deduction_ids.name', 'deduction_ids.percent')
    def _compute_moisture_percent(self):
        for rec in self:
            if rec.deduction_ids.filtered(lambda x: x.name.code == 'MD'):
                rec.moisture_percent = rec.deduction_ids.filtered(lambda x: x.name.code == 'MD').percent
            else:
                rec.moisture_percent = 0

    @api.constrains('total_gram', 'sample_weight_india', 'template_qc')
    def _check_constraint_total_gram(self):
        for record in self:
            if record.template_qc != 'husk':
                if record.picking_id.picking_type_id.code != 'production_out':
                    if record.total_gram != record.sample_weight_india:
                        raise UserError(_("Sample Weight and Total Gram need to be equal!"))
            if record.total_gram > 300:
                raise UserError(_("Total Gram need to be <= 300, please check again!"))

    @api.depends('deduction_ids', 'deduction_ids.kg', 'deduction_ids.commercial_input', 'product_qty',
                 'deduction_special_ids', 'deduction_special_ids.commercial_input', 'deduction_special_ids.kg')
    def _compute_deduction_weight_india(self):
        for record in self:
            if record.deduction_ids or record.deduction_special_ids:
                record.qty_reached = -1 * (sum(i for i in record.deduction_ids.mapped('commercial_input')) + sum(i for i in record.deduction_special_ids.mapped('commercial_input')))
                record.basis_weight = record.product_qty + record.qty_reached
            else:
                record.qty_reached = 0
                record.basis_weight = record.product_qty

    @api.depends('sample_weight', 'bb_sample_weight', 'mc_deduct', 'fm_deduct', 'broken_deduct', 'brown_deduct',
                 'check_deduction', 'picking_id.use_sample'
        , 'mold_deduct', 'excelsa_deduct', 'oversc16', 'oversc13', 'burned_deduct', 'deduction_manual', 'oversc12',
                 'oversc18', 'insect_bean_deduct')
    def _compute_deduction(self):
        return True


    @api.depends('outturn_gram')
    def compute_outturn_percent(self):
        for record in self:
            if record.outturn_gram:
                record.outturn_percent = (record.outturn_gram / 1000) * 100
            else:
                record.outturn_percent = 0

    @api.depends('aaa_gram', 'aa_gram', 'a_gram', 'b_gram', 'c_gram', 'pb_gram', 'bb_gram', 'bleached_gram', 'idb_gram',
                 'bits_gram', 'hulks_gram', 'stone_gram', 'sleeve_6_up', 'sleeve_5_5_up',
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
                                    + record.red_beans_gram + record.stinker_gram + record.faded_gram,2)
            if record.template_qc == 'bulk':
                record.total_gram = round(record.aaa_gram + record.aa_gram + record.a_gram + record.b_gram \
                                    + record.c_gram + record.pb_gram + record.bb_gram + record.bleached_gram \
                                    + record.idb_gram + record.bits_gram + record.hulks_gram + record.stone_gram \
                                    + record.skin_out_gram + record.triage_gram + record.wet_bean_gram \
                                    + record.red_beans_gram + record.stinker_gram + record.faded_gram + record.unhulled ,2)
            if record.template_qc == 'clean':
                record.total_gram = round(record.aaa_gram + record.aa_gram + record.a_gram + record.b_gram \
                                    + record.c_gram,2)
            if record.template_qc == 'clean_bulk':
                record.total_gram = round(record.aaa_gram + record.aa_gram + record.a_gram + record.b_gram \
                                          + record.c_gram + record.pb_gram, 2)
            if record.template_qc == 'c_grade':
                record.total_gram = round(record.sleeve_6_up + record.sleeve_5_5_down + record.sleeve_5_down + \
                                    record.sleeve_5_5_up,2)
            if record.template_qc == 'pb_grade':
                record.total_gram = round(record.flat_gram + record.pb1_gram + record.pb2_gram,2)
            if record.template_qc == 'lower':
                record.total_gram = round(record.good_beans + record.hulks_gram + record.unhulled + record.blacks +
                                          record.sleeve_5_up + record.bits_gram + record.stone_gram + record.idb_gram +
                                          record.bb_gram + record.triage_gram + record.remaining_coffee,2)
            if record.total_gram > 0:
                record.aaa_percent = round(record.aaa_gram / record.total_gram * 100, 2)
                record.aa_percent = round(record.aa_gram / record.total_gram * 100,2)
                record.a_percent = round(record.a_gram / record.total_gram * 100,2)
                record.b_percent = round(record.b_gram / record.total_gram * 100,2)
                record.c_percent = round(record.c_gram / record.total_gram * 100,2)
                record.pb_percent = round(record.pb_gram / record.total_gram * 100,2)
                record.bb_percent = round(record.bb_gram / record.total_gram * 100,2)
                record.bleached_percent = round(record.bleached_gram / record.total_gram * 100,2)
                record.idb_percent = round(record.idb_gram / record.total_gram * 100,2)
                record.bits_percent = round(record.bits_gram / record.total_gram * 100,2)
                record.hulks_percent = round(record.hulks_gram / record.total_gram * 100,2)
                record.stone_percent = round(record.stone_gram / record.total_gram * 100,2)
                record.skin_out_percent = round(record.skin_out_gram / record.total_gram * 100,2)
                record.triage_percent = round(record.triage_gram / record.total_gram * 100,2)
                record.wet_bean_percent = round(record.wet_bean_gram / record.total_gram * 100,2)
                record.red_beans_percent = round(record.red_beans_gram / record.total_gram * 100,2)
                record.stinker_percent = round(record.stinker_gram / record.total_gram * 100,2)
                record.faded_percent = round(record.faded_gram / record.total_gram * 100,2)
                record.flat_percent = round(record.flat_gram / record.total_gram * 100,2)
                record.pb1_percent = round(record.pb1_gram / record.total_gram * 100,2)
                record.pb2_percent = round(record.pb2_gram / record.total_gram * 100,2)
                record.sleeve_6_up_percent = round(record.sleeve_6_up / record.total_gram * 100,2)
                record.sleeve_5_5_up_percent = round(record.sleeve_5_5_up / record.total_gram * 100,2)
                record.sleeve_5_5_down_percent = round(record.sleeve_5_5_down / record.total_gram * 100,2)
                record.sleeve_5_down_percent = round(record.sleeve_5_down / record.total_gram * 100,2)

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
                 'sleeve_5_5_up_percent', 'sleeve_5_5_down_percent', 'sleeve_5_down_percent', 'total_gram',
                 'sleeve_5_up_percent', 'unhulled_percent', 'remaining_coffee_percent', 'blacks_percent', 'half_monsoon_percent', 'good_beans_percent')
    def compute_total_percent(self):
        for record in self:
            record.total_percent = 0
            if record.template_qc == 'raw':
                record.total_percent = round(record.aaa_percent + record.aa_percent + record.a_percent \
                                       + record.b_percent + record.c_percent + record.pb_percent + record.bb_percent \
                                       + record.bleached_percent + record.idb_percent + record.bits_percent \
                                       + record.hulks_percent + record.stone_percent + record.skin_out_percent \
                                       + record.triage_percent + record.wet_bean_percent + record.red_beans_percent \
                                       + record.stinker_percent + record.faded_percent, 2)
            if record.template_qc == 'bulk':
                record.total_percent = record.aaa_percent + record.aa_percent + record.a_percent \
                                       + record.b_percent + record.c_percent + record.pb_percent + record.bb_percent \
                                       + record.bleached_percent + record.idb_percent + record.bits_percent \
                                       + record.hulks_percent + record.stone_percent + record.skin_out_percent \
                                       + record.triage_percent + record.wet_bean_percent + record.red_beans_percent \
                                       + record.stinker_percent + record.faded_percent + record.unhulled_percent
            if record.template_qc == 'clean':
                record.total_percent = round(record.aaa_percent + record.aa_percent + record.a_percent \
                                       + record.b_percent + record.c_percent, 2)
            if record.template_qc == 'clean_bulk':
                record.total_percent = round(record.aaa_percent + record.aa_percent + record.a_percent \
                                       + record.b_percent + record.c_percent + record.pb_percent, 2)
            if record.template_qc == 'c_grade':
                record.total_percent = round(record.sleeve_6_up_percent + record.sleeve_5_5_up_percent \
                                       + record.sleeve_5_5_down_percent + record.sleeve_5_down_percent, 2)
            if record.template_qc == 'pb_grade':
                record.total_percent = round(record.flat_percent + record.pb1_percent + record.pb2_percent, 2)
            if record.template_qc == 'lower':
                record.total_percent = round(record.good_beans_percent + record.hulks_percent + record.unhulled_percent + record.blacks_percent +
                                          record.sleeve_5_up_percent + record.bits_percent + record.stone_percent + record.idb_percent +
                                          record.bb_percent + record.triage_percent + record.remaining_coffee_percent,2)
            if record.total_gram == 300:
                record.total_percent = 100
