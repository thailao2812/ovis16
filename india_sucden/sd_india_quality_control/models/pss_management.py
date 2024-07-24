# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError


class PSSManagement(models.Model):
    _inherit = "pss.management"

    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')

    outturn_percent = fields.Float(string='Outturn%', digits=(12, 2))
    aaa_percent = fields.Float(string="AAA%",  )
    aa_percent = fields.Float(string="AA%",  )
    a_percent = fields.Float(string="A%",  )
    b_percent = fields.Float(string="B%",  )
    c_percent = fields.Float(string="C%",  )
    pb_percent = fields.Float(string="PB%",  )
    bb_percent = fields.Float(string="BB%",  )
    bleached_percent = fields.Float(string="Bleached%",  )
    idb_percent = fields.Float(string="IDB%",  )
    bits_percent = fields.Float(string="Bits%",  )
    hulks_percent = fields.Float(string="Husk%",  )
    stone_percent = fields.Float(string="Stone%",  )
    skin_out_percent = fields.Float(string='Skin Out%',  )
    triage_percent = fields.Float(string='Triage%',  )
    wet_bean_percent = fields.Float(string='Wet Beans%',  )
    red_beans_percent = fields.Float(string='Red Beans%',  )
    stinker_percent = fields.Float(string='Stinker%',  )
    faded_percent = fields.Float(string='Faded%',  )
    flat_percent = fields.Float(string='Flat%',  )
    pb1_percent = fields.Float(string='PB1%',  )
    pb2_percent = fields.Float(string='PB2%',  )
    sleeve_6_up_percent = fields.Float(string='6↑ %',  )
    sleeve_5_5_up_percent = fields.Float(string='5.5↑ %',  )
    sleeve_5_5_down_percent = fields.Float(string='5.5↓%',  )
    sleeve_5_down_percent = fields.Float(string='5↓ %',  )

    sleeve_5_up_percent = fields.Float(string='5↑ %',  )
    unhulled_percent = fields.Float(string='Unhulled %',  )
    remaining_coffee_percent = fields.Float(string='Remaining Coffee %',  )
    blacks_percent = fields.Float(string='Blacks %',  )
    half_monsoon_percent = fields.Float(string='Half Monsoon %',  )
    good_beans_percent = fields.Float(string='Good Beans %',  )

    moisture_percent = fields.Float(string='Moisture%', digits=(12, 2),  )

    @api.onchange('stack')
    def onchange_stack(self):
        res = super(PSSManagement, self).onchange_stack()
        for i in self:
            if not i.stack:
                i.outturn_percent = 0
                i.aaa_percent = 0
                i.aa_percent = 0
                i.a_percent = 0
                i.b_percent = 0
                i.c_percent = 0
                i.pb_percent = 0
                i.bb_percent = 0
                i.bleached_percent = 0
                i.idb_percent = 0
                i.bits_percent = 0
                i.hulks_percent = 0
                i.stone_percent = 0
                i.skin_out_percent = 0
                i.triage_percent = 0
                i.wet_bean_percent = 0
                i.red_beans_percent = 0
                i.stinker_percent = 0
                i.faded_percent = 0
                i.flat_percent = 0
                i.pb1_percent = 0
                i.pb2_percent = 0
                i.sleeve_6_up_percent = 0
                i.sleeve_5_5_up_percent = 0
                i.sleeve_5_5_down_percent = 0
                i.sleeve_5_down_percent = 0
                i.moisture_percent = 0


            for stack in i.stack:
                i.outturn_percent = stack.outturn_percent
                i.aaa_percent = stack.aaa_percent
                i.aa_percent = stack.aa_percent
                i.a_percent = stack.a_percent
                i.b_percent = stack.b_percent
                i.c_percent = stack.c_percent
                i.pb_percent = stack.pb_percent
                i.bb_percent = stack.bb_percent
                i.bleached_percent = stack.bleached_percent
                i.idb_percent = stack.idb_percent
                i.bits_percent = stack.bits_percent
                i.hulks_percent = stack.hulks_percent
                i.stone_percent = stack.stone_percent
                i.skin_out_percent = stack.skin_out_percent
                i.triage_percent = stack.triage_percent
                i.wet_bean_percent = stack.wet_bean_percent
                i.red_beans_percent = stack.red_beans_percent
                i.stinker_percent = stack.stinker_percent
                i.faded_percent = stack.faded_percent
                i.flat_percent = stack.flat_percent
                i.pb1_percent = stack.pb1_percent
                i.pb2_percent = stack.pb2_percent
                i.sleeve_6_up_percent = stack.sleeve_6_up_percent
                i.sleeve_5_5_up_percent = stack.sleeve_5_5_up_percent
                i.sleeve_5_5_down_percent = stack.sleeve_5_5_down_percent
                i.sleeve_5_down_percent = stack.sleeve_5_down_percent

                i.sleeve_5_up_percent = stack.sleeve_5_up_percent
                i.unhulled_percent = stack.unhulled_percent
                i.remaining_coffee_percent = stack.remaining_coffee_percent
                i.blacks_percent = stack.blacks_percent
                i.half_monsoon_percent = stack.half_monsoon_percent
                i.good_beans_percent = stack.good_beans_percent

                i.moisture_percent = stack.moisture_percent

        return res