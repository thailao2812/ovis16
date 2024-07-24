# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from datetime import datetime, date, timedelta

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
import time
from odoo.exceptions import ValidationError, UserError


class StockLot(models.Model):
    _inherit = 'stock.lot'

    outturn_percent = fields.Float(string='Outturn%', compute='compute_qc_india', store=True, digits=(12, 2))
    aaa_percent = fields.Float(string="AAA%", compute='compute_qc_india', store=True)
    aa_percent = fields.Float(string="AA%", compute='compute_qc_india', store=True)
    a_percent = fields.Float(string="A%", compute='compute_qc_india', store=True)
    b_percent = fields.Float(string="B%", compute='compute_qc_india', store=True)
    c_percent = fields.Float(string="C%", compute='compute_qc_india', store=True)
    pb_percent = fields.Float(string="PB%", compute='compute_qc_india', store=True)
    bb_percent = fields.Float(string="BB%", compute='compute_qc_india', store=True)
    bleached_percent = fields.Float(string="Bleached%", compute='compute_qc_india', store=True)
    idb_percent = fields.Float(string="IDB%", compute='compute_qc_india', store=True)
    bits_percent = fields.Float(string="Bits%", compute='compute_qc_india', store=True)
    hulks_percent = fields.Float(string="Husk%", compute='compute_qc_india', store=True)
    stone_percent = fields.Float(string="Stone%", compute='compute_qc_india', store=True)
    skin_out_percent = fields.Float(string='Skin Out%', compute='compute_qc_india', store=True)
    triage_percent = fields.Float(string='Triage%', compute='compute_qc_india', store=True)
    wet_bean_percent = fields.Float(string='Wet Beans%', compute='compute_qc_india', store=True)
    red_beans_percent = fields.Float(string='Red Beans%', compute='compute_qc_india', store=True)
    stinker_percent = fields.Float(string='Stinker%', compute='compute_qc_india', store=True)
    faded_percent = fields.Float(string='Faded%', compute='compute_qc_india', store=True)
    flat_percent = fields.Float(string='Flat%', compute='compute_qc_india', store=True)
    pb1_percent = fields.Float(string='PB1%', compute='compute_qc_india', store=True)
    pb2_percent = fields.Float(string='PB2%', compute='compute_qc_india', store=True)
    sleeve_6_up_percent = fields.Float(string='6↑ %', compute='compute_qc_india', store=True)
    sleeve_5_5_up_percent = fields.Float(string='5.5↑ %', compute='compute_qc_india', store=True)
    sleeve_5_5_down_percent = fields.Float(string='5.5↓%', compute='compute_qc_india', store=True)
    sleeve_5_down_percent = fields.Float(string='5↓ %', compute='compute_qc_india', store=True)
    moisture_percent = fields.Float(string='Moisture%', digits=(12, 2), compute='compute_qc_india', store=True)

    sleeve_5_up_percent = fields.Float(string='5↑ %', digits=(12, 2), compute='compute_qc_india', store=True)
    unhulled_percent = fields.Float(string='Unhulled %', digits=(12, 2), compute='compute_qc_india', store=True)
    remaining_coffee_percent = fields.Float(string='Remaining Coffee %', digits=(12, 2), compute='compute_qc_india', store=True)
    blacks_percent = fields.Float(string='Blacks %', digits=(12, 2), compute='compute_qc_india', store=True)
    half_monsoon_percent = fields.Float(string='Half Monsoon %', digits=(12, 2), compute='compute_qc_india', store=True)
    good_beans_percent = fields.Float(string='Good Beans %', digits=(12, 2), compute='compute_qc_india', store=True)

    # old field
    net_qty = fields.Float(compute='compute_qc_india', string="NET Qty", digits=(12, 0), store=True)
    basis_qty = fields.Float(compute='compute_qc_india', string="Basis Qty", digits=(12, 0), store=True)

    gdn_basis = fields.Float(compute='compute_qc_india', string="Gdn Basis Qty", digits=(12, 0), store=True)
    gdn_net = fields.Float(compute='compute_qc_india', string="Gdn Net Qty", digits=(12, 0), store=True)

    gip_net = fields.Float(compute='compute_qc_india', string="Gip Net Qty", digits=(12, 0), store=True)
    gip_basis = fields.Float(compute='compute_qc_india', string="Gip Basis Qty", digits=(12, 0), store=True)

    contract_no = fields.Char(string="Contract No", compute='compute_qc_india', store=True)
    districts_id = fields.Many2one('res.district', compute='compute_qc_india', string='Source', store=True)

    @api.depends('move_line_ids',
                 'move_line_ids.picking_id.state_kcs',
                 'move_line_ids.picking_id.state',
                 'move_line_ids.picking_id.kcs_line',
                 'move_line_ids.init_qty')
    def _compute_qc(self):
        return True

    @api.depends('move_line_ids',
                 'move_line_ids.picking_id.state_kcs',
                 'move_line_ids.picking_id.state',
                 'move_line_ids.picking_id.kcs_line',
                 'move_line_ids.init_qty', 'init_invetory')
    def compute_qc_india(self):
        for this in self:
            outturn_percent = aaa_percent = aa_percent = a_percent = b_percent = c_percent = \
                pb_percent = bb_percent = bleached_percent = idb_percent = bits_percent = \
                hulks_percent = stone_percent = skin_out_percent = triage_percent = wet_bean_percent = \
                red_beans_percent = stinker_percent = faded_percent = flat_percent = pb1_percent = pb2_percent = \
                sleeve_6_up_percent = sleeve_5_5_up_percent = sleeve_5_5_down_percent = \
                sleeve_5_down_percent = moisture_percent = sleeve_5_up_percent = unhulled_percent = \
                blacks_percent = half_monsoon_percent = good_beans_percent = remaining_coffee_percent =  count = 0
            gip_net = gip_basis = gdn_basis = gdn_net = net_qty = basis_qty = 0.0
            packing_id = districts_id = production_id = False
            if this.move_line_ids:
                packing_id = this.move_line_ids[0].picking_id.packing_id and this.move_line_ids[0].picking_id.packing_id.id
            for line in this.move_line_ids:
                if line.picking_id.picking_type_id.code in ('production_in', 'transfer_in', 'incoming'):
                    if line.state != 'done':
                        continue

                    for kcs in line.picking_id.kcs_line:
                        if kcs.stack_id.id == this.id:
                            outturn_percent += kcs.outturn_percent * line.init_qty or 0.0
                            aaa_percent += kcs.aaa_percent * line.init_qty or 0.0
                            aa_percent += kcs.aa_percent * line.init_qty or 0.0
                            a_percent += kcs.a_percent * line.init_qty or 0.0
                            b_percent += kcs.b_percent * line.init_qty or 0.0
                            c_percent += kcs.c_percent * line.init_qty or 0.0
                            pb_percent += kcs.pb_percent * line.init_qty or 0.0
                            bb_percent += kcs.bb_percent * line.init_qty or 0.0
                            bleached_percent += kcs.bleached_percent * line.init_qty or 0.0
                            idb_percent += kcs.idb_percent * line.init_qty or 0.0
                            bits_percent += kcs.bits_percent * line.init_qty or 0.0
                            hulks_percent += kcs.hulks_percent * line.init_qty or 0.0
                            stone_percent += kcs.stone_percent * line.init_qty or 0.0
                            skin_out_percent += kcs.skin_out_percent * line.init_qty or 0.0
                            triage_percent += kcs.triage_percent * line.init_qty or 0.0
                            wet_bean_percent += kcs.wet_bean_percent * line.init_qty or 0.0
                            red_beans_percent += kcs.red_beans_percent * line.init_qty or 0.0
                            stinker_percent += kcs.stinker_percent * line.init_qty or 0.0
                            faded_percent += kcs.faded_percent * line.init_qty or 0.0
                            flat_percent += kcs.flat_percent * line.init_qty or 0.0
                            pb1_percent += kcs.pb1_percent * line.init_qty or 0.0
                            pb2_percent += kcs.pb2_percent * line.init_qty or 0.0
                            sleeve_6_up_percent += kcs.sleeve_6_up_percent * line.init_qty or 0.0
                            sleeve_5_5_up_percent += kcs.sleeve_5_5_up_percent * line.init_qty or 0.0
                            sleeve_5_5_down_percent += kcs.sleeve_5_5_down_percent * line.init_qty or 0.0
                            sleeve_5_down_percent += kcs.sleeve_5_down_percent * line.init_qty or 0.0
                            moisture_percent += kcs.moisture_percent * line.init_qty or 0.0

                            sleeve_5_up_percent += kcs.sleeve_5_up_percent * line.init_qty or 0.0
                            unhulled_percent += kcs.unhulled_percent * line.init_qty or 0.0
                            blacks_percent += kcs.blacks_percent * line.init_qty or 0.0
                            half_monsoon_percent += kcs.half_monsoon_percent * line.init_qty or 0.0
                            good_beans_percent += kcs.good_beans_percent * line.init_qty or 0.0
                            remaining_coffee_percent += kcs.remaining_coffee_percent * line.init_qty or 0.0

                            count += line.init_qty


                    net_qty += line.init_qty
                    basis_qty += line.qty_done

                    if line.picking_id.districts_id:
                        districts_id = line.picking_id.districts_id.id

                    if line.picking_id.production_id:
                        production_id = line.picking_id.production_id.id

                # packing_id = line.picking_id.packing_id and line.picking_id.packing_id.id
                if line.picking_id.picking_type_id.code in ('outgoing', 'transfer_out') and line.state == 'done':
                    gdn_basis += line.qty_done
                    gdn_net += line.init_qty
                if line.picking_id.picking_type_id.code == 'production_out' and line.state == 'done':
                    gip_net += line.init_qty
                    gip_basis += line.qty_done
            if this.init_invetory:
                this.update({'packing_id': packing_id,
                             'net_qty': this.init_invetory_qty,
                             'basis_qty': basis_qty,
                             'gdn_basis': gdn_basis,
                             'gdn_net': gdn_net,
                             'gip_net': gip_net,
                             'gip_basis': gip_basis,
                             'production_id': production_id,
                             'districts_id': districts_id})
            else:
                this.update({'outturn_percent': count != 0 and outturn_percent / count or 0.0,
                             'aaa_percent': count != 0 and aaa_percent / count or 0.0,
                             'aa_percent': count != 0 and aa_percent / count or 0.0,
                             'a_percent': count != 0 and a_percent / count or 0.0,
                             'b_percent': count != 0 and b_percent / count or 0.0,
                             'c_percent': count != 0 and c_percent / count or 0.0,
                             'pb_percent': count != 0 and pb_percent / count or 0.0,
                             'bb_percent': count != 0 and bb_percent / count or 0.0,
                             'bleached_percent': count != 0 and bleached_percent / count or 0.0,
                             'idb_percent': count != 0 and idb_percent / count or 0.0,
                             'bits_percent': count != 0 and bits_percent / count or 0.0,
                             'hulks_percent': count != 0 and hulks_percent / count or 0.0,
                             'stone_percent': count != 0 and stone_percent / count or 0.0,
                             'skin_out_percent': count != 0 and skin_out_percent / count or 0.0,
                             'triage_percent': count != 0 and triage_percent / count or 0.0,
                             'wet_bean_percent': count != 0 and wet_bean_percent / count or 0.0,
                             'red_beans_percent': count != 0 and red_beans_percent / count or 0.0,
                             'stinker_percent': count != 0 and stinker_percent / count or 0.0,
                             'faded_percent': count != 0 and faded_percent / count or 0.0,
                             'flat_percent': count != 0 and flat_percent / count or 0.0,
                             'pb1_percent': count != 0 and pb1_percent / count or 0.0,
                             'pb2_percent': count != 0 and pb2_percent / count or 0.0,
                             'sleeve_6_up_percent': count != 0 and sleeve_6_up_percent / count or 0.0,
                             'sleeve_5_5_up_percent': count != 0 and sleeve_5_5_up_percent / count or 0.0,
                             'sleeve_5_5_down_percent': count != 0 and sleeve_5_5_down_percent / count or 0.0,
                             'sleeve_5_down_percent': count != 0 and sleeve_5_down_percent / count or 0.0,
                             'moisture_percent': count != 0 and moisture_percent / count or 0.0,

                             'sleeve_5_up_percent': count != 0 and sleeve_5_up_percent / count or 0.0,
                             'unhulled_percent': count != 0 and unhulled_percent / count or 0.0,
                             'blacks_percent': count != 0 and blacks_percent / count or 0.0,
                             'half_monsoon_percent': count != 0 and half_monsoon_percent / count or 0.0,
                             'good_beans_percent': count != 0 and good_beans_percent / count or 0.0,
                             'remaining_coffee_percent': count != 0 and remaining_coffee_percent / count or 0.0,

                             'packing_id': packing_id,
                             'net_qty': net_qty,
                             'basis_qty': basis_qty,
                             'gdn_basis': gdn_basis,
                             'gdn_net': gdn_net,
                             'gip_net': gip_net,
                             'gip_basis': gip_basis,
                             'production_id': production_id,
                             'districts_id': districts_id})




