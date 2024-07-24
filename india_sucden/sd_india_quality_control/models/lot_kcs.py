# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError


class LotKCS(models.Model):
    _inherit = "lot.kcs"

    outturn_percent = fields.Float(string='Outturn%', compute='_compute_qc_india', store=True, digits=(12, 2))
    aaa_percent = fields.Float(string="AAA%", compute='_compute_qc_india', store=True,)
    aa_percent = fields.Float(string="AA%", compute='_compute_qc_india', store=True,)
    a_percent = fields.Float(string="A%", compute='_compute_qc_india', store=True,)
    b_percent = fields.Float(string="B%", compute='_compute_qc_india', store=True,)
    c_percent = fields.Float(string="C%", compute='_compute_qc_india', store=True, )
    pb_percent = fields.Float(string="PB%", compute='_compute_qc_india', store=True, )
    bb_percent = fields.Float(string="BB%", compute='_compute_qc_india', store=True,)
    bleached_percent = fields.Float(string="Bleached%", compute='_compute_qc_india', store=True, )
    idb_percent = fields.Float(string="IDB%", compute='_compute_qc_india', store=True,)
    bits_percent = fields.Float(string="Bits%", compute='_compute_qc_india', store=True,)
    hulks_percent = fields.Float(string="Husk%", compute='_compute_qc_india', store=True,)
    stone_percent = fields.Float(string="Stone%", compute='_compute_qc_india', store=True,)
    skin_out_percent = fields.Float(string='Skin Out%', compute='_compute_qc_india', store=True,)
    triage_percent = fields.Float(string='Triage%', compute='_compute_qc_india', store=True,)
    wet_bean_percent = fields.Float(string='Wet Beans%', compute='_compute_qc_india', store=True,)
    red_beans_percent = fields.Float(string='Red Beans%', compute='_compute_qc_india', store=True,)
    stinker_percent = fields.Float(string='Stinker%', compute='_compute_qc_india', store=True,)
    faded_percent = fields.Float(string='Faded%', compute='_compute_qc_india', store=True,)
    flat_percent = fields.Float(string='Flat%', compute='_compute_qc_india', store=True,)
    pb1_percent = fields.Float(string='PB1%', compute='_compute_qc_india', store=True,)
    pb2_percent = fields.Float(string='PB2%', compute='_compute_qc_india', store=True,)
    sleeve_6_up_percent = fields.Float(string='6↑ %', compute='_compute_qc_india', store=True,)
    sleeve_5_5_up_percent = fields.Float(string='5.5↑ %', compute='_compute_qc_india', store=True,)
    sleeve_5_5_down_percent = fields.Float(string='5.5↓%', compute='_compute_qc_india', store=True,)
    sleeve_5_down_percent = fields.Float(string='5↓ %', compute='_compute_qc_india', store=True,)
    moisture_percent = fields.Float(string='Moisture%', digits=(12, 2), compute='_compute_qc_india', store=True,)

    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')

    @api.depends('quantity', 'los_ids', 'los_ids.quantity', 'los_ids.stack_id', 'los_ids.grp_id', 'state',
                 'los_ids.grp_id.state_kcs')
    def _compute_qc_india(self):
        for line in self:
            outturn_percent = aaa_percent = aa_percent = a_percent = b_percent = c_percent = pb_percent = bb_percent = bleached_percent = idb_percent = \
                bits_percent = hulks_percent = stone_percent = skin_out_percent = triage_percent = wet_bean_percent = red_beans_percent = \
                stinker_percent = faded_percent = flat_percent = pb1_percent = pb2_percent = sleeve_6_up_percent = sleeve_5_5_up_percent = \
                sleeve_5_5_down_percent = sleeve_5_down_percent = moisture_percent = 0.0
            count = 0
            for lot in line.los_ids:
                outturn_percent += lot.stack_id.outturn_percent * lot.quantity or 0.0
                aaa_percent += lot.stack_id.aaa_percent * lot.quantity or 0.0
                aa_percent += lot.stack_id.aa_percent * lot.quantity or 0.0
                a_percent += lot.stack_id.a_percent * lot.quantity or 0.0
                b_percent += lot.stack_id.b_percent * lot.quantity or 0.0
                c_percent += lot.stack_id.c_percent * lot.quantity or 0.0
                pb_percent += lot.stack_id.pb_percent * lot.quantity or 0.0
                bb_percent += lot.stack_id.bb_percent * lot.quantity or 0.0
                bleached_percent += lot.stack_id.bleached_percent * lot.quantity or 0.0
                idb_percent += lot.stack_id.idb_percent * lot.quantity or 0.0
                bits_percent += lot.stack_id.bits_percent * lot.quantity or 0.0
                hulks_percent += lot.stack_id.hulks_percent * lot.quantity or 0.0
                stone_percent += lot.stack_id.stone_percent * lot.quantity or 0.0
                skin_out_percent += lot.stack_id.skin_out_percent * lot.quantity or 0.0
                triage_percent += lot.stack_id.triage_percent * lot.quantity or 0.0
                wet_bean_percent += lot.stack_id.wet_bean_percent * lot.quantity or 0.0
                red_beans_percent += lot.stack_id.red_beans_percent * lot.quantity or 0.0
                stinker_percent += lot.stack_id.stinker_percent * lot.quantity or 0.0
                faded_percent += lot.stack_id.faded_percent * lot.quantity or 0.0
                flat_percent += lot.stack_id.flat_percent * lot.quantity or 0.0
                pb1_percent += lot.stack_id.pb1_percent * lot.quantity or 0.0
                pb2_percent += lot.stack_id.pb2_percent * lot.quantity or 0.0
                sleeve_6_up_percent += lot.stack_id.sleeve_6_up_percent * lot.quantity or 0.0
                sleeve_5_5_up_percent += lot.stack_id.sleeve_5_5_up_percent * lot.quantity or 0.0
                sleeve_5_5_down_percent += lot.stack_id.sleeve_5_5_down_percent * lot.quantity or 0.0
                sleeve_5_down_percent += lot.stack_id.sleeve_5_down_percent * lot.quantity or 0.0
                moisture_percent += lot.stack_id.moisture_percent * lot.quantity or 0.0
                count += lot.quantity

            line.outturn_percent = count and outturn_percent / count or 0.0
            line.aaa_percent = count and aaa_percent / count or 0.0
            line.aa_percent = count and aa_percent / count or 0.0
            line.a_percent = count and a_percent / count or 0.0
            line.b_percent = count and b_percent / count or 0.0
            line.c_percent = count and c_percent / count or 0.0
            line.pb_percent = count and pb_percent / count or 0.0
            line.bb_percent = count and bb_percent / count or 0.0
            line.bleached_percent = count and bleached_percent / count or 0.0
            line.idb_percent = count and idb_percent / count or 0.0
            line.bits_percent = count and bits_percent / count or 0.0
            line.hulks_percent = count and hulks_percent / count or 0.0
            line.stone_percent = count and stone_percent / count or 0.0
            line.skin_out_percent = count and skin_out_percent / count or 0.0
            line.triage_percent = count and triage_percent / count or 0.0
            line.wet_bean_percent = count and wet_bean_percent / count or 0.0
            line.red_beans_percent = count and red_beans_percent / count or 0.0
            line.stinker_percent = count and stinker_percent / count or 0.0
            line.faded_percent = count and faded_percent / count or 0.0
            line.flat_percent = count and flat_percent / count or 0.0
            line.pb1_percent = count and pb1_percent / count or 0.0
            line.pb2_percent = count and pb2_percent / count or 0.0
            line.sleeve_6_up_percent = count and sleeve_6_up_percent / count or 0.0
            line.sleeve_5_5_up_percent = count and sleeve_5_5_up_percent / count or 0.0
            line.sleeve_5_5_down_percent = count and sleeve_5_5_down_percent / count or 0.0
            line.sleeve_5_down_percent = count and sleeve_5_down_percent / count or 0.0
            line.moisture_percent = count and moisture_percent / count or 0.0
