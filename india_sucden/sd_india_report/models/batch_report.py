# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict
import re
DATE_FORMAT = "%Y-%m-%d"

class BatchReport(models.Model):
    _name = 'batch.report'
    _order = 'production_id desc'
    _description = 'Batch Report'
    
    
    
    production_id = fields.Many2one('mrp.production',string="Production", domain=[('state', '=', 'done')])
    name = fields.Char(string="Name", default=lambda self: _('New'))
    input_ids = fields.One2many('batch.report.input','batch_id',string="Inputs")
    outputs_ids = fields.One2many('batch.report.output','batch_id',string="OutPus")
    instore_ids = fields.One2many('batch.report.instore','batch_id', string='In-store')
    
    @api.model
    def create(self,vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['mrp.production'].search([('id','=',vals['production_id'])]).name
        return super(BatchReport, self).create(vals)
    
    def export_datas(self):
        return self.env.ref(
                'sd_india_report.batch_report').report_action(self)
                
    def load_data(self):
        for this in self:
            sql ='''
                DELETE FROM batch_report_input where batch_id = %s ;
                DELETE FROM batch_report_output where batch_id = %s ;
                DELETE FROM batch_report_instore where batch_id = %s ;
                
                
                SELECT spt.code as picking_type_code,
                        sp.id,
                        sml.lot_id as stack_id,
                        DATE(timezone('UTC', sp.date_done::timestamp)) date_done
                FROM stock_picking sp join stock_move_line sml on sp.id = sml.picking_id
                    join stock_picking_type spt on sp.picking_type_id = spt.id
                WHERE (sml.finished_id = %s or sml.material_id = %s)
                    AND spt.code in ('production_in','production_out')
                    AND sp.state ='done'
            '''%(this.id,this.id,this.id, this.production_id.id, this.production_id.id)
            self.env.cr.execute(sql)
            for line in self.env.cr.dictfetchall():
                
                val ={
                    'stack_id':line['stack_id'],
                    'picking_id':line['id'],
                    'date': line['date_done'],
                    'batch_id':this.id
                    }
                if line['picking_type_code'] == 'production_out':
                    self.env['batch.report.input'].create(val)
                else:
                    if self.env['stock.picking'].search([('id','=',line['id'])]).categ_id.code != 'Loss':
                        self.env['batch.report.output'].create(val)
            self.create_instore()
        
        self.input_ids.refresh()
        self.outputs_ids.refresh()
        self.instore_ids.refresh()
        
        
        self.compute_ins_qc()
        self.compute_in_qc()
        self.compute_out_qc()
        return

    def compute_in_qc(self):
        for this in self:
            if this.input_ids and sum([x.real_qty for x in this.input_ids]) > 0:
                sql = '''
                    SELECT
                        SUM(mc*net_qty)/SUM(net_qty) mc,
                        sum(fm*net_qty)/sum(net_qty) fm,
                        sum(black*net_qty)/sum(net_qty) black,
                        sum(broken*net_qty)/sum(net_qty) broken,
                        sum(brown*net_qty)/sum(net_qty) brown,
                        sum(mold*net_qty)/sum(net_qty) mold,
                        sum(cherry*net_qty)/sum(net_qty) cherry,
                        sum(excelsa*net_qty)/sum(net_qty) excelsa,
                        sum(screen20*net_qty)/sum(net_qty) screen20,
                        sum(screen19*net_qty)/sum(net_qty) screen19,
                        sum(screen18*net_qty)/sum(net_qty) screen18,
                        sum(screen16*net_qty)/sum(net_qty) screen16,
                        sum(screen13*net_qty)/sum(net_qty) screen13,
                        sum(screen12*net_qty)/sum(net_qty) screen12,
                        sum(greatersc12*net_qty)/sum(net_qty) greatersc12,
                        sum(burn*net_qty)/sum(net_qty) burn,
                        sum(immature*net_qty)/sum(net_qty) immature,
                        
                        sum(outturn_percent*net_qty)/sum(net_qty) in_outturn,
                        sum(aaa_percent*net_qty)/sum(net_qty) in_aaa,
                        sum(aa_percent*net_qty)/sum(net_qty) in_aa,
                        sum(a_percent*net_qty)/sum(net_qty) in_a,
                        sum(b_percent*net_qty)/sum(net_qty) in_b,
                        sum(c_percent*net_qty)/sum(net_qty) in_c,
                        sum(pb_percent*net_qty)/sum(net_qty) in_pb,
                        sum(bb_percent*net_qty)/sum(net_qty) in_bb,
                        sum(bleached_percent*net_qty)/sum(net_qty) in_bleach,
                        sum(idb_percent*net_qty)/sum(net_qty) in_idb,
                        sum(bits_percent*net_qty)/sum(net_qty) in_bits,
                        sum(hulks_percent*net_qty)/sum(net_qty) in_husk,
                        sum(stone_percent*net_qty)/sum(net_qty) in_stone,
                        sum(skin_out_percent*net_qty)/sum(net_qty) in_skin_out,
                        sum(triage_percent*net_qty)/sum(net_qty) in_triage,
                        sum(wet_bean_percent*net_qty)/sum(net_qty) in_wet_bean,
                        sum(red_beans_percent*net_qty)/sum(net_qty) in_red_bean,
                        sum(stinker_percent*net_qty)/sum(net_qty) in_stinker,
                        sum(faded_percent*net_qty)/sum(net_qty) in_faded,
                        sum(flat_percent*net_qty)/sum(net_qty) in_flat,
                        sum(pb1_percent*net_qty)/sum(net_qty) in_pb1,
                        sum(pb2_percent*net_qty)/sum(net_qty) in_pb2,
                        sum(sleeve_6_up_percent*net_qty)/sum(net_qty) in_6_up,
                        sum(sleeve_5_5_up_percent*net_qty)/sum(net_qty) in_5_5_up,
                        sum(sleeve_5_5_down_percent*net_qty)/sum(net_qty) in_5_5_down,
                        sum(sleeve_5_down_percent*net_qty)/sum(net_qty) in_5_down,
                        
                        sum(sleeve_5_up_percent*net_qty)/sum(net_qty) in_sleeve_5_up_percent,
                        sum(unhulled_percent*net_qty)/sum(net_qty) in_unhulled_percent,
                        sum(remaining_coffee_percent*net_qty)/sum(net_qty) in_remaining_coffee_percent,
                        sum(blacks_percent*net_qty)/sum(net_qty) in_blacks_percent,
                        sum(half_monsoon_percent*net_qty)/sum(net_qty) in_half_monsoon_percent,
                        sum(good_beans_percent*net_qty)/sum(net_qty) in_good_beans_percent,
                        
                        sum(moisture_percent*net_qty)/sum(net_qty) in_moisture,
                        
                        sum(net_qty) total_in_qty,
                        sum(real_qty) total_real_qty,
                        sum(bag_no) total_bag
                    FROM batch_report_input
                    WHERE batch_id = %s
                    '''%(this.id)
                # print(sql)
                self._cr.execute(sql)
                for line in self._cr.dictfetchall():
                    this.update({
                        'in_mc': line['mc'],
                        'in_fm': line['fm'],
                        'in_black': line['black'],
                        'in_broken': line['broken'],
                        'in_brown': line['brown'],
                        'in_mold': line['mold'],
                        'in_cherry': line['cherry'],
                        'in_excelsa': line['excelsa'],
                        'in_screen20': line['screen20'],
                        'in_screen19': line['screen19'],
                        'in_screen18': line['screen18'],
                        'in_screen16': line['screen16'],
                        'in_screen13': line['screen13'],
                        'in_screen12': line['screen12'],
                        'in_greatersc12': line['greatersc12'],
                        'in_burn': line['burn'],
                        'in_immature': line['immature'],
                        'total_in_qty': line['total_in_qty'],
                        'total_real_qty': line['total_real_qty'],
                        'total_bag': line['total_bag'],

                        'in_moisture': line['in_moisture'],
                        'in_outturn': line['in_outturn'],
                        'in_aaa': line['in_aaa'],
                        'in_aa': line['in_aa'],
                        'in_a': line['in_a'],
                        'in_b': line['in_b'],
                        'in_c': line['in_c'],
                        'in_pb': line['in_pb'],
                        'in_bb': line['in_bb'],
                        'in_bleach': line['in_bleach'],
                        'in_idb': line['in_idb'],
                        'in_bits': line['in_bits'],
                        'in_husk': line['in_husk'],
                        'in_stone': line['in_stone'],
                        'in_skin_out': line['in_skin_out'],
                        'in_triage': line['in_triage'],
                        'in_wet_bean': line['in_wet_bean'],
                        'in_red_bean': line['in_red_bean'],
                        'in_stinker': line['in_stinker'],
                        'in_faded': line['in_faded'],
                        'in_flat': line['in_flat'],
                        'in_pb1': line['in_pb1'],
                        'in_pb2': line['in_pb2'],
                        'in_6_up': line['in_6_up'],
                        'in_5_5_up': line['in_5_5_up'],
                        'in_5_5_down': line['in_5_5_down'],
                        'in_5_down': line['in_5_down'],

                        'in_sleeve_5_up_percent': line['in_sleeve_5_up_percent'],
                        'in_unhulled_percent': line['in_unhulled_percent'],
                        'in_remaining_coffee_percent': line['in_remaining_coffee_percent'],
                        'in_blacks_percent': line['in_blacks_percent'],
                        'in_half_monsoon_percent': line['in_half_monsoon_percent'],
                        'in_good_beans_percent': line['in_good_beans_percent'],
                    })
    
    
    def create_instore(self):
        for this in self:
            if this.input_ids:
                sql = '''
                    SELECT stack_id
                    FROM batch_report_input
                    WHERE batch_id = %s
                    GROUP BY stack_id
                    '''%(this.id)
                self._cr.execute(sql)
                for line in self._cr.dictfetchall():
                    net_qty = sum([x.init_qty for x in self.env['stock.lot'].search([('id','=', line['stack_id'])]).move_line_ids.filtered(lambda r: r.picking_id.picking_type_id.code in ('production_in','transfer_in','incoming','phys_adj'))])
                    val ={
                        'stack_id':line['stack_id'],
                        'net_qty': net_qty or 0.0,
                        'batch_id':this.id
                        }
                    self.env['batch.report.instore'].create(val)
        return True
    
    
    in_mc = fields.Float(digits=(12,4), string='Mc',readonly=True)
    in_fm = fields.Float(digits=(12,4), string='Fm',readonly=True)
    in_black = fields.Float(digits=(12,4), string='Black',readonly=True)
    in_broken = fields.Float(digits=(12,4), string='Broken',readonly=True)
    in_brown = fields.Float(digits=(12,4), string='Brown',readonly=True)
    in_mold = fields.Float(digits=(12,4), string='Mold',readonly=True)
    in_cherry = fields.Float(string='Cherry',digits=(12,4),readonly=True)
    in_excelsa = fields.Float(digits=(12,4), string='Excelsa',readonly=True)
    in_screen20 = fields.Float(string =">20%", digits=(12,4),readonly=True)
    in_screen19 = fields.Float(string =">19%", digits=(12,4),readonly=True)
    in_screen18 = fields.Float(string =">18%", digits=(12,4),readonly=True)
    in_screen16 = fields.Float(string =">16%", digits=(12,4),readonly=True)
    in_screen13 = fields.Float(string =">13%", digits=(12,4),readonly=True)
    in_screen12 = fields.Float(string ="<12%", digits=(12,4),readonly=True)
    in_greatersc12 = fields.Float(string =">12%", digits=(12,4),readonly=True)
    in_burn = fields.Float(string ="Burn", digits=(12,4),readonly=True)
    in_immature = fields.Float(string ="Immature", digits=(12,4),readonly=True)
    total_in_qty = fields.Float(string='Total In Qty', digits=(12,4),readonly=True)
    total_real_qty = fields.Float(string='Total Real Qty', digits=(12,4),readonly=True)
    total_bag = fields.Float(string='Total Bag', digits=(12,4),readonly=True)

    in_moisture = fields.Float(digits=(12,4), string='Moisture %',readonly=True)
    in_outturn = fields.Float(digits=(12,4), string='Outturn %',readonly=True)
    in_aaa = fields.Float(digits=(12,4), string='AAA %',readonly=True)
    in_aa = fields.Float(digits=(12,4), string='AA %',readonly=True)
    in_a = fields.Float(digits=(12,4), string='A %',readonly=True)
    in_b = fields.Float(digits=(12,4), string='B %',readonly=True)
    in_c = fields.Float(digits=(12,4), string='C %',readonly=True)
    in_pb = fields.Float(digits=(12,4), string='PB %',readonly=True)
    in_bb = fields.Float(digits=(12,4), string='BB %',readonly=True)
    in_bleach = fields.Float(digits=(12,4), string='Bleached %',readonly=True)
    in_idb = fields.Float(digits=(12,4), string='IDB %',readonly=True)
    in_bits = fields.Float(digits=(12,4), string='Bits %',readonly=True)
    in_husk = fields.Float(digits=(12,4), string='Husk %',readonly=True)
    in_stone = fields.Float(digits=(12,4), string='Stone %',readonly=True)
    in_skin_out = fields.Float(digits=(12,4), string='Skin Out %',readonly=True)
    in_triage = fields.Float(digits=(12,4), string='Triage %',readonly=True)
    in_wet_bean = fields.Float(digits=(12,4), string='Wet bean %',readonly=True)
    in_red_bean = fields.Float(digits=(12,4), string='Red Bean %',readonly=True)
    in_stinker = fields.Float(digits=(12,4), string='Stinker %',readonly=True)
    in_faded = fields.Float(digits=(12,4), string='Faded %',readonly=True)
    in_flat = fields.Float(digits=(12,4), string='Flat %',readonly=True)
    in_pb1 = fields.Float(digits=(12,4), string='PB1 %',readonly=True)
    in_pb2 = fields.Float(digits=(12,4), string='PB2 %',readonly=True)
    in_6_up = fields.Float(digits=(12,4), string='6↑ %',readonly=True)
    in_5_5_up = fields.Float(digits=(12,4), string='5.5↑ %',readonly=True)
    in_5_5_down = fields.Float(digits=(12,4), string='5.5↓ %',readonly=True)
    in_5_down = fields.Float(digits=(12,4), string='5↓ %',readonly=True)

    in_sleeve_5_up_percent = fields.Float(digits=(12,4), string='5↑ %',readonly=True)
    in_unhulled_percent = fields.Float(digits=(12,4), string='Unhulled %',readonly=True)
    in_remaining_coffee_percent = fields.Float(digits=(12,4), string='Remaining Coffee %',readonly=True)
    in_blacks_percent = fields.Float(digits=(12,4), string='Blacks %',readonly=True)
    in_half_monsoon_percent = fields.Float(digits=(12,4), string='Half Monsoon %',readonly=True)
    in_good_beans_percent = fields.Float(digits=(12,4), string='Good Beans %',readonly=True)

    def compute_ins_qc(self):
        for this in self:
            if this.instore_ids and sum([x.net_qty for x in this.instore_ids]) > 0:
                sql = '''
                    SELECT
                        SUM(mc*net_qty)/SUM(net_qty) mc,
                        sum(fm*net_qty)/sum(net_qty) fm,
                        sum(black*net_qty)/sum(net_qty) black,
                        sum(broken*net_qty)/sum(net_qty) broken,
                        sum(brown*net_qty)/sum(net_qty) brown,
                        sum(mold*net_qty)/sum(net_qty) mold,
                        sum(cherry*net_qty)/sum(net_qty) cherry,
                        sum(excelsa*net_qty)/sum(net_qty) excelsa,
                        sum(screen20*net_qty)/sum(net_qty) screen20,
                        sum(screen19*net_qty)/sum(net_qty) screen19,
                        sum(screen18*net_qty)/sum(net_qty) screen18,
                        sum(screen16*net_qty)/sum(net_qty) screen16,
                        sum(screen13*net_qty)/sum(net_qty) screen13,
                        sum(screen12*net_qty)/sum(net_qty) screen12,
                        sum(greatersc12*net_qty)/sum(net_qty) greatersc12,
                        sum(burn*net_qty)/sum(net_qty) burn,
                        sum(eaten*net_qty)/sum(net_qty) eaten,
                        sum(immature*net_qty)/sum(net_qty) immature,
                        sum(net_qty) total_instore_qty,
                        
                        sum(outturn_percent*net_qty)/sum(net_qty) ins_outturn,
                        sum(aaa_percent*net_qty)/sum(net_qty) ins_aaa,
                        sum(aa_percent*net_qty)/sum(net_qty) ins_aa,
                        sum(a_percent*net_qty)/sum(net_qty) ins_a,
                        sum(b_percent*net_qty)/sum(net_qty) ins_b,
                        sum(c_percent*net_qty)/sum(net_qty) ins_c,
                        sum(pb_percent*net_qty)/sum(net_qty) ins_pb,
                        sum(bb_percent*net_qty)/sum(net_qty) ins_bb,
                        sum(bleached_percent*net_qty)/sum(net_qty) ins_bleach,
                        sum(idb_percent*net_qty)/sum(net_qty) ins_idb,
                        sum(bits_percent*net_qty)/sum(net_qty) ins_bits,
                        sum(hulks_percent*net_qty)/sum(net_qty) ins_husk,
                        sum(stone_percent*net_qty)/sum(net_qty) ins_stone,
                        sum(skin_out_percent*net_qty)/sum(net_qty) ins_skin_out,
                        sum(triage_percent*net_qty)/sum(net_qty) ins_triage,
                        sum(wet_bean_percent*net_qty)/sum(net_qty) ins_wet_bean,
                        sum(red_beans_percent*net_qty)/sum(net_qty) ins_red_bean,
                        sum(stinker_percent*net_qty)/sum(net_qty) ins_stinker,
                        sum(faded_percent*net_qty)/sum(net_qty) ins_faded,
                        sum(flat_percent*net_qty)/sum(net_qty) ins_flat,
                        sum(pb1_percent*net_qty)/sum(net_qty) ins_pb1,
                        sum(pb2_percent*net_qty)/sum(net_qty) ins_pb2,
                        sum(sleeve_6_up_percent*net_qty)/sum(net_qty) ins_6_up,
                        sum(sleeve_5_5_up_percent*net_qty)/sum(net_qty) ins_5_5_up,
                        sum(sleeve_5_5_down_percent*net_qty)/sum(net_qty) ins_5_5_down,
                        sum(sleeve_5_down_percent*net_qty)/sum(net_qty) ins_5_down,
                        
                        sum(sleeve_5_up_percent*net_qty)/sum(net_qty) ins_sleeve_5_up_percent,
                        sum(unhulled_percent*net_qty)/sum(net_qty) ins_unhulled_percent,
                        sum(remaining_coffee_percent*net_qty)/sum(net_qty) ins_remaining_coffee_percent,
                        sum(blacks_percent*net_qty)/sum(net_qty) ins_blacks_percent,
                        sum(half_monsoon_percent*net_qty)/sum(net_qty) ins_half_monsoon_percent,
                        sum(good_beans_percent*net_qty)/sum(net_qty) ins_good_beans_percent,
                        
                        sum(moisture_percent*net_qty)/sum(net_qty) ins_moisture
                        
                    FROM batch_report_instore
                    WHERE batch_id = %s
                    '''%(this.id)
                self._cr.execute(sql)
                for line in self._cr.dictfetchall():
                    this.update({
                        'ins_mc': line['mc'],
                        'ins_fm': line['fm'],
                        'ins_black': line['black'],
                        'ins_broken': line['broken'],
                        'ins_brown': line['brown'],
                        'ins_mold': line['mold'],
                        'ins_cherry': line['cherry'],
                        'ins_excelsa': line['excelsa'],
                        'ins_screen20': line['screen20'],
                        'ins_screen19': line['screen19'],
                        'ins_screen18': line['screen18'],
                        'ins_screen16': line['screen16'],
                        'ins_screen13': line['screen13'],
                        'ins_screen12': line['screen12'],
                        'ins_greatersc12': line['greatersc12'],
                        'ins_burn': line['burn'],
                        'ins_eaten':line['eaten'],
                        'ins_immature': line['immature'],
                        'total_instore_qty': line['total_instore_qty'],

                        'ins_moisture': line['ins_moisture'],
                        'ins_outturn': line['ins_outturn'],
                        'ins_aaa': line['ins_aaa'],
                        'ins_aa': line['ins_aa'],
                        'ins_a': line['ins_a'],
                        'ins_b': line['ins_b'],
                        'ins_c': line['ins_c'],
                        'ins_pb': line['ins_pb'],
                        'ins_bb': line['ins_bb'],
                        'ins_bleach': line['ins_bleach'],
                        'ins_idb': line['ins_idb'],
                        'ins_bits': line['ins_bits'],
                        'ins_husk': line['ins_husk'],
                        'ins_stone': line['ins_stone'],
                        'ins_skin_out': line['ins_skin_out'],
                        'ins_triage': line['ins_triage'],
                        'ins_wet_bean': line['ins_wet_bean'],
                        'ins_red_bean': line['ins_red_bean'],
                        'ins_stinker': line['ins_stinker'],
                        'ins_faded': line['ins_faded'],
                        'ins_flat': line['ins_flat'],
                        'ins_pb1': line['ins_pb1'],
                        'ins_pb2': line['ins_pb2'],
                        'ins_6_up': line['ins_6_up'],
                        'ins_5_5_up': line['ins_5_5_up'],
                        'ins_5_5_down': line['ins_5_5_down'],
                        'ins_5_down': line['ins_5_down'],

                        'ins_sleeve_5_up_percent': line['ins_sleeve_5_up_percent'],
                        'ins_unhulled_percent': line['ins_unhulled_percent'],
                        'ins_remaining_coffee_percent': line['ins_remaining_coffee_percent'],
                        'ins_blacks_percent': line['ins_blacks_percent'],
                        'ins_half_monsoon_percent': line['ins_half_monsoon_percent'],
                        'ins_good_beans_percent': line['ins_good_beans_percent'],
                    })

    ins_mc = fields.Float(digits=(12,4), string='Mc',readonly=True)
    ins_fm = fields.Float(digits=(12,4), string='Fm', readonly=True)
    ins_black = fields.Float(digits=(12,4), string='Black', readonly=True)
    ins_broken = fields.Float(digits=(12,4), string='Broken', readonly=True)
    ins_brown = fields.Float(digits=(12,4), string='Brown', readonly=True)
    ins_mold = fields.Float(digits=(12,4), string='Mold', readonly=True)
    ins_cherry = fields.Float(readonly=True, digits=(12,4), string='Cherry')
    ins_excelsa = fields.Float(readonly=True, digits=(12,4), string='Excelsa')
    ins_screen20 = fields.Float(string =">20%", readonly=True, digits=(12,4))
    ins_screen19 = fields.Float(string =">19%", readonly=True, digits=(12,4))
    ins_screen18 = fields.Float(string =">18%", readonly=True, digits=(12,4))
    ins_screen16 = fields.Float(string =">16%", readonly=True, digits=(12,4))
    ins_screen13 = fields.Float(string =">13%", readonly=True, digits=(12,4))
    ins_screen12 = fields.Float(string ="<12%", readonly=True, digits=(12,4))
    ins_greatersc12 = fields.Float( string =">12%", readonly=True, digits=(12,4))
    ins_burn = fields.Float(string ="Burn", readonly=True, digits=(12,4))
    ins_eaten = fields.Float(digits=(12,4), string='Eaten',readonly=True)
    ins_immature = fields.Float(string ="Immature", readonly=True, digits=(12,4))
    total_instore_qty = fields.Float(string='Total Instore Qty',readonly=True)

    ins_moisture = fields.Float(digits=(12, 4), string='Moisture %', readonly=True)
    ins_outturn = fields.Float(digits=(12, 4), string='Outturn %', readonly=True)
    ins_aaa = fields.Float(digits=(12, 4), string='AAA %', readonly=True)
    ins_aa = fields.Float(digits=(12, 4), string='AA %', readonly=True)
    ins_a = fields.Float(digits=(12, 4), string='A %', readonly=True)
    ins_b = fields.Float(digits=(12, 4), string='B %', readonly=True)
    ins_c = fields.Float(digits=(12, 4), string='C %', readonly=True)
    ins_pb = fields.Float(digits=(12, 4), string='PB %', readonly=True)
    ins_bb = fields.Float(digits=(12, 4), string='BB %', readonly=True)
    ins_bleach = fields.Float(digits=(12, 4), string='Bleached %', readonly=True)
    ins_idb = fields.Float(digits=(12, 4), string='IDB %', readonly=True)
    ins_bits = fields.Float(digits=(12, 4), string='Bits %', readonly=True)
    ins_husk = fields.Float(digits=(12, 4), string='Husk %', readonly=True)
    ins_stone = fields.Float(digits=(12, 4), string='Stone %', readonly=True)
    ins_skin_out = fields.Float(digits=(12, 4), string='Skin Out %', readonly=True)
    ins_triage = fields.Float(digits=(12, 4), string='Triage %', readonly=True)
    ins_wet_bean = fields.Float(digits=(12, 4), string='Wet bean %', readonly=True)
    ins_red_bean = fields.Float(digits=(12, 4), string='Red Bean %', readonly=True)
    ins_stinker = fields.Float(digits=(12, 4), string='Stinker %', readonly=True)
    ins_faded = fields.Float(digits=(12, 4), string='Faded %', readonly=True)
    ins_flat = fields.Float(digits=(12, 4), string='Flat %', readonly=True)
    ins_pb1 = fields.Float(digits=(12, 4), string='PB1 %', readonly=True)
    ins_pb2 = fields.Float(digits=(12, 4), string='PB2 %', readonly=True)
    ins_6_up = fields.Float(digits=(12, 4), string='6↑ %', readonly=True)
    ins_5_5_up = fields.Float(digits=(12, 4), string='5.5↑ %', readonly=True)
    ins_5_5_down = fields.Float(digits=(12, 4), string='5.5↓ %', readonly=True)
    ins_5_down = fields.Float(digits=(12, 4), string='5↓ %', readonly=True)

    ins_sleeve_5_up_percent = fields.Float(digits=(12, 4), string='5↑ %', readonly=True)
    ins_unhulled_percent = fields.Float(digits=(12, 4), string='Unhulled %', readonly=True)
    ins_remaining_coffee_percent = fields.Float(digits=(12, 4), string='Remaining Coffee %', readonly=True)
    ins_blacks_percent = fields.Float(digits=(12, 4), string='Blacks %', readonly=True)
    ins_half_monsoon_percent = fields.Float(digits=(12, 4), string='Half Monsoon %', readonly=True)
    ins_good_beans_percent = fields.Float(digits=(12, 4), string='Good Beans %', readonly=True)


    def input_line(self):
        for rec in self.input_ids:
            print(rec.aaa_percent)

    
    def compute_out_qc(self):
        for this in self:
            if this.outputs_ids and sum([x.net_qty for x in this.outputs_ids]) > 0:
                sql = '''
                    SELECT
                        SUM(mc*net_qty)/SUM(net_qty) mc,
                        sum(fm*net_qty)/sum(net_qty) fm,
                        sum(black*net_qty)/sum(net_qty) black,
                        sum(broken*net_qty)/sum(net_qty) broken,
                        sum(brown*net_qty)/sum(net_qty) brown,
                        sum(mold*net_qty)/sum(net_qty) mold,
                        sum(cherry*net_qty)/sum(net_qty) cherry,
                        sum(excelsa*net_qty)/sum(net_qty) excelsa,
                        sum(screen20*net_qty)/sum(net_qty) screen20,
                        sum(screen19*net_qty)/sum(net_qty) screen19,
                        sum(screen18*net_qty)/sum(net_qty) screen18,
                        sum(screen16*net_qty)/sum(net_qty) screen16,
                        sum(screen13*net_qty)/sum(net_qty) screen13,
                        sum(screen12*net_qty)/sum(net_qty) screen12,
                        sum(greatersc12*net_qty)/sum(net_qty) greatersc12,
                        sum(burn*net_qty)/sum(net_qty) burn,
                        sum(immature*net_qty)/sum(net_qty) immature,
                        sum(net_qty) total_out_qty,
                        
                        sum(outturn_percent*net_qty)/sum(net_qty) out_outturn,
                        sum(aaa_percent*net_qty)/sum(net_qty) out_aaa,
                        sum(aa_percent*net_qty)/sum(net_qty) out_aa,
                        sum(a_percent*net_qty)/sum(net_qty) out_a,
                        sum(b_percent*net_qty)/sum(net_qty) out_b,
                        sum(c_percent*net_qty)/sum(net_qty) out_c,
                        sum(pb_percent*net_qty)/sum(net_qty) out_pb,
                        sum(bb_percent*net_qty)/sum(net_qty) out_bb,
                        sum(bleached_percent*net_qty)/sum(net_qty) out_bleach,
                        sum(idb_percent*net_qty)/sum(net_qty) out_idb,
                        sum(bits_percent*net_qty)/sum(net_qty) out_bits,
                        sum(hulks_percent*net_qty)/sum(net_qty) out_husk,
                        sum(stone_percent*net_qty)/sum(net_qty) out_stone,
                        sum(skin_out_percent*net_qty)/sum(net_qty) out_skin_out,
                        sum(triage_percent*net_qty)/sum(net_qty) out_triage,
                        sum(wet_bean_percent*net_qty)/sum(net_qty) out_wet_bean,
                        sum(red_beans_percent*net_qty)/sum(net_qty) out_red_bean,
                        sum(stinker_percent*net_qty)/sum(net_qty) out_stinker,
                        sum(faded_percent*net_qty)/sum(net_qty) out_faded,
                        sum(flat_percent*net_qty)/sum(net_qty) out_flat,
                        sum(pb1_percent*net_qty)/sum(net_qty) out_pb1,
                        sum(pb2_percent*net_qty)/sum(net_qty) out_pb2,
                        sum(sleeve_6_up_percent*net_qty)/sum(net_qty) out_6_up,
                        sum(sleeve_5_5_up_percent*net_qty)/sum(net_qty) out_5_5_up,
                        sum(sleeve_5_5_down_percent*net_qty)/sum(net_qty) out_5_5_down,
                        sum(sleeve_5_down_percent*net_qty)/sum(net_qty) out_5_down,
                        
                        sum(sleeve_5_up_percent*net_qty)/sum(net_qty) out_sleeve_5_up_percent,
                        sum(unhulled_percent*net_qty)/sum(net_qty) out_unhulled_percent,
                        sum(remaining_coffee_percent*net_qty)/sum(net_qty) out_remaining_coffee_percent,
                        sum(blacks_percent*net_qty)/sum(net_qty) out_blacks_percent,
                        sum(half_monsoon_percent*net_qty)/sum(net_qty) out_half_monsoon_percent,
                        sum(good_beans_percent*net_qty)/sum(net_qty) out_good_beans_percent,
                        
                        sum(moisture_percent*net_qty)/sum(net_qty) out_moisture
                        
                    FROM batch_report_output
                    WHERE batch_id = %s
                    '''%(this.id)
                self._cr.execute(sql)
                for line in self._cr.dictfetchall():
                    this.update({
                        'out_mc': line['mc'],
                        'out_fm': line['fm'],
                        'out_black': line['black'],
                        'out_broken': line['broken'],
                        'out_brown': line['brown'],
                        'out_mold': line['mold'],
                        'out_cherry': line['cherry'],
                        'out_excelsa': line['excelsa'],
                        'out_screen20': line['screen20'],
                        'out_screen19': line['screen19'],
                        'out_screen18': line['screen18'],
                        'out_screen16': line['screen16'],
                        'out_screen13': line['screen13'],
                        'out_screen12': line['screen12'],
                        'out_greatersc12': line['greatersc12'],
                        'out_burn': line['burn'],
                        'out_immature': line['immature'],
                        'total_out_qty': line['total_out_qty'],

                        'out_moisture': line['out_moisture'],
                        'out_outturn': line['out_outturn'],
                        'out_aaa': line['out_aaa'],
                        'out_aa': line['out_aa'],
                        'out_a': line['out_a'],
                        'out_b': line['out_b'],
                        'out_c': line['out_c'],
                        'out_pb': line['out_pb'],
                        'out_bb': line['out_bb'],
                        'out_bleach': line['out_bleach'],
                        'out_idb': line['out_idb'],
                        'out_bits': line['out_bits'],
                        'out_husk': line['out_husk'],
                        'out_stone': line['out_stone'],
                        'out_skin_out': line['out_skin_out'],
                        'out_triage': line['out_triage'],
                        'out_wet_bean': line['out_wet_bean'],
                        'out_red_bean': line['out_red_bean'],
                        'out_stinker': line['out_stinker'],
                        'out_faded': line['out_faded'],
                        'out_flat': line['out_flat'],
                        'out_pb1': line['out_pb1'],
                        'out_pb2': line['out_pb2'],
                        'out_6_up': line['out_6_up'],
                        'out_5_5_up': line['out_5_5_up'],
                        'out_5_5_down': line['out_5_5_down'],
                        'out_5_down': line['out_5_down'],

                        'out_sleeve_5_up_percent': line['out_sleeve_5_up_percent'],
                        'out_unhulled_percent': line['out_unhulled_percent'],
                        'out_remaining_coffee_percent': line['out_remaining_coffee_percent'],
                        'out_blacks_percent': line['out_blacks_percent'],
                        'out_half_monsoon_percent': line['out_half_monsoon_percent'],
                        'out_good_beans_percent': line['out_good_beans_percent'],
                    })
    
    out_mc = fields.Float(digits=(12,4), string='Mc',readonly=True)
    out_fm = fields.Float(digits=(12,4), string='Fm',readonly=True)
    out_black = fields.Float(digits=(12,4), string='Black',readonly=True)
    out_broken = fields.Float(digits=(12,4), string='Broken',readonly=True)
    out_brown = fields.Float(digits=(12,4), string='Brown',readonly=True)
    out_mold = fields.Float(digits=(12,4), string='Mold',readonly=True)
    out_cherry = fields.Float(digits=(12,4), string='Cherry',readonly=True)
    out_excelsa = fields.Float(digits=(12,4), string='Excelsa',readonly=True)
    out_screen20 = fields.Float(string =">20%", digits=(12,4),readonly=True)
    out_screen19 = fields.Float(string =">19%", digits=(12,4),readonly=True)
    out_screen18 = fields.Float(string =">18%", digits=(12,4),readonly=True)
    out_screen16 = fields.Float(string =">16%", digits=(12,4),readonly=True)
    out_screen13 = fields.Float(string =">13%", digits=(12,4),readonly=True)
    out_screen12 = fields.Float(string ="<12%", digits=(12,4),readonly=True)
    out_greatersc12 = fields.Float(string =">12%", digits=(12,4),readonly=True)
    out_burn = fields.Float(string ="Burn", digits=(12,4),readonly=True)
    out_immature = fields.Float(string ="Immature", digits=(12,4),readonly=True)
    total_out_qty = fields.Float(string='Total Out Qty', digits=(12,4),readonly=True)

    out_moisture = fields.Float(digits=(12, 4), string='Moisture %', readonly=True)
    out_outturn = fields.Float(digits=(12, 4), string='Outturn %', readonly=True)
    out_aaa = fields.Float(digits=(12, 4), string='AAA %', readonly=True)
    out_aa = fields.Float(digits=(12, 4), string='AA %', readonly=True)
    out_a = fields.Float(digits=(12, 4), string='A %', readonly=True)
    out_b = fields.Float(digits=(12, 4), string='B %', readonly=True)
    out_c = fields.Float(digits=(12, 4), string='C %', readonly=True)
    out_pb = fields.Float(digits=(12, 4), string='PB %', readonly=True)
    out_bb = fields.Float(digits=(12, 4), string='BB %', readonly=True)
    out_bleach = fields.Float(digits=(12, 4), string='Bleached %', readonly=True)
    out_idb = fields.Float(digits=(12, 4), string='IDB %', readonly=True)
    out_bits = fields.Float(digits=(12, 4), string='Bits %', readonly=True)
    out_husk = fields.Float(digits=(12, 4), string='Husk %', readonly=True)
    out_stone = fields.Float(digits=(12, 4), string='Stone %', readonly=True)
    out_skin_out = fields.Float(digits=(12, 4), string='Skin Out %', readonly=True)
    out_triage = fields.Float(digits=(12, 4), string='Triage %', readonly=True)
    out_wet_bean = fields.Float(digits=(12, 4), string='Wet bean %', readonly=True)
    out_red_bean = fields.Float(digits=(12, 4), string='Red Bean %', readonly=True)
    out_stinker = fields.Float(digits=(12, 4), string='Stinker %', readonly=True)
    out_faded = fields.Float(digits=(12, 4), string='Faded %', readonly=True)
    out_flat = fields.Float(digits=(12, 4), string='Flat %', readonly=True)
    out_pb1 = fields.Float(digits=(12, 4), string='PB1 %', readonly=True)
    out_pb2 = fields.Float(digits=(12, 4), string='PB2 %', readonly=True)
    out_6_up = fields.Float(digits=(12, 4), string='6↑ %', readonly=True)
    out_5_5_up = fields.Float(digits=(12, 4), string='5.5↑ %', readonly=True)
    out_5_5_down = fields.Float(digits=(12, 4), string='5.5↓ %', readonly=True)
    out_5_down = fields.Float(digits=(12, 4), string='5↓ %', readonly=True)

    out_sleeve_5_up_percent = fields.Float(digits=(12, 4), string='5↑ %', readonly=True)
    out_unhulled_percent = fields.Float(digits=(12, 4), string='Unhulled %', readonly=True)
    out_remaining_coffee_percent = fields.Float(digits=(12, 4), string='Remaining Coffee %', readonly=True)
    out_blacks_percent = fields.Float(digits=(12, 4), string='Blacks %', readonly=True)
    out_half_monsoon_percent = fields.Float(digits=(12, 4), string='Half Monsoon %', readonly=True)
    out_good_beans_percent = fields.Float(digits=(12, 4), string='Good Beans %', readonly=True)

class BatchReportInput(models.Model):
    _name = "batch.report.input"

    outturn_percent = fields.Float(string='Outturn%', compute='compute_qc', store=True, digits=(12, 2))
    aaa_percent = fields.Float(string="AAA%", compute='compute_qc', store=True, digits=(12, 2))
    aa_percent = fields.Float(string="AA%", compute='compute_qc', store=True, digits=(12, 2))
    a_percent = fields.Float(string="A%", compute='compute_qc', store=True, digits=(12, 2))
    b_percent = fields.Float(string="B%", compute='compute_qc', store=True, digits=(12, 2))
    c_percent = fields.Float(string="C%", compute='compute_qc', store=True, digits=(12, 2))
    pb_percent = fields.Float(string="PB%", compute='compute_qc', store=True, digits=(12, 2))
    bb_percent = fields.Float(string="BB%", compute='compute_qc', store=True, digits=(12, 2))
    bleached_percent = fields.Float(string="Bleached%", compute='compute_qc', store=True, digits=(12, 2))
    idb_percent = fields.Float(string="IDB%", compute='compute_qc', store=True, digits=(12, 2))
    bits_percent = fields.Float(string="Bits%", compute='compute_qc', store=True, digits=(12, 2))
    hulks_percent = fields.Float(string="Husk%", compute='compute_qc', store=True, digits=(12, 2))
    stone_percent = fields.Float(string="Stone%", compute='compute_qc', store=True, digits=(12, 2))
    skin_out_percent = fields.Float(string='Skin Out%', compute='compute_qc', store=True, digits=(12, 2))
    triage_percent = fields.Float(string='Triage%', compute='compute_qc', store=True, digits=(12, 2))
    wet_bean_percent = fields.Float(string='Wet Beans%', compute='compute_qc', store=True, digits=(12, 2))
    red_beans_percent = fields.Float(string='Red Beans%', compute='compute_qc', store=True, digits=(12, 2))
    stinker_percent = fields.Float(string='Stinker%', compute='compute_qc', store=True, digits=(12, 2))
    faded_percent = fields.Float(string='Faded%', compute='compute_qc', store=True, digits=(12, 2))
    flat_percent = fields.Float(string='Flat%', compute='compute_qc', store=True, digits=(12, 2))
    pb1_percent = fields.Float(string='PB1%', compute='compute_qc', store=True, digits=(12, 2))
    pb2_percent = fields.Float(string='PB2%', compute='compute_qc', store=True, digits=(12, 2))
    sleeve_6_up_percent = fields.Float(string='6↑ %', compute='compute_qc', store=True, digits=(12, 2))
    sleeve_5_5_up_percent = fields.Float(string='5.5↑ %', compute='compute_qc', store=True, digits=(12, 2))
    sleeve_5_5_down_percent = fields.Float(string='5.5↓%', compute='compute_qc', store=True, digits=(12, 2))
    sleeve_5_down_percent = fields.Float(string='5↓ %', compute='compute_qc', store=True, digits=(12, 2))

    sleeve_5_up_percent = fields.Float(string='5↑ %', compute='compute_qc', store=True, digits=(12, 2))
    unhulled_percent = fields.Float(string='Unhulled %', compute='compute_qc', store=True, digits=(12, 2))
    remaining_coffee_percent = fields.Float(string='Remaining Coffee %', compute='compute_qc', store=True, digits=(12, 2))
    blacks_percent = fields.Float(string='Blacks %', compute='compute_qc', store=True, digits=(12, 2))
    half_monsoon_percent = fields.Float(string='Half Monsoon %', compute='compute_qc', store=True, digits=(12, 2))
    good_beans_percent = fields.Float(string='Good Beans %', compute='compute_qc', store=True, digits=(12, 2))

    moisture_percent = fields.Float(string='Moisture%', digits=(12, 2), compute='compute_qc', store=True)

    @api.depends('picking_id')
    def compute_qc(self):
        for this in self:
            if this.picking_id:
                for move in this.picking_id.move_line_ids_without_package.filtered(lambda r: r.product_id.id == this.product_id.id):
                    this.update({
                        'bag_no': move.bag_no,
                        'packing_id': move.packing_id,
                        'net_qty': move.init_qty,
                        'real_qty': move.init_qty,
                    })
                for kcs in this.picking_id.kcs_line.filtered(lambda r: r.product_id.id == this.product_id.id):
                    this.update({
                        'mc': kcs.mc,
                        'fm': kcs.fm,
                        'black': kcs.black,
                        'broken': kcs.broken,
                        'brown': kcs.brown,
                        'mold': kcs.mold,
                        'cherry': kcs.cherry,
                        'excelsa': kcs.excelsa,
                        'screen20': kcs.screen20,
                        'screen19': kcs.screen19,
                        'screen18': kcs.screen18,
                        'screen16': kcs.screen16,
                        'screen13': kcs.screen13,
                        'screen12': kcs.belowsc12,
                        'greatersc12': kcs.greatersc12,
                        'burn': kcs.burned,
                        'eaten': kcs.eaten,
                        'stone_count': kcs.stone_count or False,
                        'stick_count': kcs.stick_count or False,
                        'immature': kcs.immature,

                        'outturn_percent': kcs.outturn_percent,
                        'aaa_percent': kcs.aaa_percent,
                        'aa_percent': kcs.aa_percent,
                        'a_percent': kcs.a_percent,
                        'b_percent': kcs.b_percent,
                        'c_percent': kcs.c_percent,
                        'pb_percent': kcs.pb_percent,
                        'bb_percent': kcs.bb_percent,
                        'bleached_percent': kcs.bleached_percent,
                        'idb_percent': kcs.idb_percent,
                        'bits_percent': kcs.bits_percent,
                        'hulks_percent': kcs.hulks_percent,
                        'stone_percent': kcs.stone_percent,
                        'skin_out_percent': kcs.skin_out_percent,
                        'triage_percent': kcs.triage_percent,
                        'wet_bean_percent': kcs.wet_bean_percent,
                        'red_beans_percent': kcs.red_beans_percent,
                        'stinker_percent': kcs.stinker_percent,
                        'faded_percent': kcs.faded_percent,
                        'flat_percent': kcs.flat_percent,
                        'pb1_percent': kcs.pb1_percent,
                        'pb2_percent': kcs.pb2_percent,
                        'sleeve_6_up_percent': kcs.sleeve_6_up_percent,
                        'sleeve_5_5_up_percent': kcs.sleeve_5_5_up_percent,
                        'sleeve_5_5_down_percent': kcs.sleeve_5_5_down_percent,
                        'sleeve_5_down_percent': kcs.sleeve_5_down_percent,
                        'moisture_percent': kcs.moisture_percent,
                    })
    stack_id = fields.Many2one('stock.lot',string="Stack No.")
    picking_id = fields.Many2one('stock.picking',string="Gip")
    date = fields.Date(string='Date')
    zone_id = fields.Many2one('stock.zone',string='Zone', related='stack_id.zone_id', store=True)

    net_qty = fields.Float(compute='compute_qc', store=True, string ="Net Weight")
    real_qty = fields.Float(compute='compute_qc', store=True, string ="Real Weight")

    product_id = fields.Many2one('product.product',string="Product.",related='stack_id.product_id', store=True)
    categ_id = fields.Many2one('product.category', string='Category',related='stack_id.product_id.categ_id', store=True)
    bag_no = fields.Float(string='Bag No', compute='compute_qc', store=True)
    packing_id = fields.Many2one('ned.packing', string='Packing',compute='compute_qc', store=True)

    mc = fields.Float(compute='compute_qc', store=True, string='Mc')
    fm = fields.Float(compute='compute_qc', store=True, string='Fm')
    black = fields.Float(compute='compute_qc', store=True, string='Black')
    broken = fields.Float(compute='compute_qc', store=True, string='Broken')
    brown = fields.Float(compute='compute_qc', store=True, string='Brown')
    mold = fields.Float(compute='compute_qc', store=True, string='Mold')
    cherry = fields.Float(compute='compute_qc' ,store=True, string='Cherry')
    excelsa = fields.Float(compute='compute_qc' ,store=True, string='Excelsa')
    screen20 = fields.Float(compute='compute_qc', string =">20%", store=True)
    screen19 = fields.Float(compute='compute_qc', string =">19%", store=True)
    screen18 = fields.Float(compute='compute_qc', string =">18%", store=True)
    screen16 = fields.Float(compute='compute_qc', string =">16%", store=True)
    screen13 = fields.Float(compute='compute_qc', string =">13%", store=True)
    screen12 = fields.Float(compute='compute_qc', string ="<12%", store=True)
    greatersc12 = fields.Float(compute='compute_qc', string =">12%", store=True)
    burn = fields.Float(compute='compute_qc', string ="Burn", store=True)
    eaten = fields.Float(compute='compute_qc', string ="Eaten", store=True)
    immature = fields.Float(compute='compute_qc', string ="Immature", store=True)
    state = fields.Selection(related='picking_id.state', string='State')
    batch_id = fields.Many2one('batch.report', string="Inputs")
    
    
    stone_count = fields.Float(compute='compute_qc', string='Stone Count', store=True)
    stick_count = fields.Float(compute='compute_qc', string='Stick Count', store=True)
    
    
class BatchReportOutput(models.Model):
    _name = "batch.report.output"

    outturn_percent = fields.Float(string='Outturn%', compute='compute_qc', store=True, digits=(12, 2))
    aaa_percent = fields.Float(string="AAA%", compute='compute_qc', store=True)
    aa_percent = fields.Float(string="AA%", compute='compute_qc', store=True)
    a_percent = fields.Float(string="A%", compute='compute_qc', store=True)
    b_percent = fields.Float(string="B%", compute='compute_qc', store=True)
    c_percent = fields.Float(string="C%", compute='compute_qc', store=True)
    pb_percent = fields.Float(string="PB%", compute='compute_qc', store=True)
    bb_percent = fields.Float(string="BB%", compute='compute_qc', store=True)
    bleached_percent = fields.Float(string="Bleached%", compute='compute_qc', store=True)
    idb_percent = fields.Float(string="IDB%", compute='compute_qc', store=True)
    bits_percent = fields.Float(string="Bits%", compute='compute_qc', store=True)
    hulks_percent = fields.Float(string="Husk%", compute='compute_qc', store=True)
    stone_percent = fields.Float(string="Stone%", compute='compute_qc', store=True)
    skin_out_percent = fields.Float(string='Skin Out%', compute='compute_qc', store=True)
    triage_percent = fields.Float(string='Triage%', compute='compute_qc', store=True)
    wet_bean_percent = fields.Float(string='Wet Beans%', compute='compute_qc', store=True)
    red_beans_percent = fields.Float(string='Red Beans%', compute='compute_qc', store=True)
    stinker_percent = fields.Float(string='Stinker%', compute='compute_qc', store=True)
    faded_percent = fields.Float(string='Faded%', compute='compute_qc', store=True)
    flat_percent = fields.Float(string='Flat%', compute='compute_qc', store=True)
    pb1_percent = fields.Float(string='PB1%', compute='compute_qc', store=True)
    pb2_percent = fields.Float(string='PB2%', compute='compute_qc', store=True)
    sleeve_6_up_percent = fields.Float(string='6↑ %', compute='compute_qc', store=True)
    sleeve_5_5_up_percent = fields.Float(string='5.5↑ %', compute='compute_qc', store=True)
    sleeve_5_5_down_percent = fields.Float(string='5.5↓%', compute='compute_qc', store=True)
    sleeve_5_down_percent = fields.Float(string='5↓ %', compute='compute_qc', store=True)

    sleeve_5_up_percent = fields.Float(string='5↑ %', compute='compute_qc', store=True)
    unhulled_percent = fields.Float(string='Unhulled %', compute='compute_qc', store=True)
    remaining_coffee_percent = fields.Float(string='Remaining Coffee %', compute='compute_qc', store=True)
    blacks_percent = fields.Float(string='Blacks %', compute='compute_qc', store=True)
    half_monsoon_percent = fields.Float(string='Half Monsoon %', compute='compute_qc', store=True)
    good_beans_percent = fields.Float(string='Good Beans %', compute='compute_qc', store=True)

    moisture_percent = fields.Float(string='Moisture%', digits=(12, 2), compute='compute_qc', store=True)

    @api.depends('picking_id')
    def compute_qc(self):
        for this in self:
            if this.picking_id:
                weightscale = 0
                for move in this.picking_id.move_line_ids_without_package.filtered(lambda r: r.product_id.id == this.product_id.id):  
                    # if move.weighbridge == 0:
                    weightscale = move.init_qty
                    # else:
                    #     weightscale = move.weighbridge

                    this.update({
                        'bag_no': move.bag_no,
                        'packing_id': move.packing_id,
                        'net_qty': weightscale,
                        'real_qty': move.init_qty
                    })
                for kcs in this.picking_id.kcs_line.filtered(lambda r: r.product_id.id == this.product_id.id):
                    this.update({
                        'mc': kcs.mc,
                        'fm': kcs.fm,
                        'black': kcs.black,
                        'broken': kcs.broken,
                        'brown': kcs.brown,
                        'mold': kcs.mold,
                        'cherry': kcs.cherry,
                        'excelsa': kcs.excelsa,
                        'screen20': kcs.screen20,
                        'screen19': kcs.screen19,
                        'screen18': kcs.screen18,
                        'screen16': kcs.screen16,
                        'screen13': kcs.screen13,
                        'screen12': kcs.belowsc12,
                        'greatersc12': kcs.greatersc12,
                        'burn': kcs.burned,
                        'eaten': kcs.eaten,
                        'stone_count': kcs.stone_count,
                        'stick_count': kcs.stick_count,
                        'immature': kcs.immature,

                        'outturn_percent': kcs.outturn_percent,
                        'aaa_percent': kcs.aaa_percent,
                        'aa_percent': kcs.aa_percent,
                        'a_percent': kcs.a_percent,
                        'b_percent': kcs.b_percent,
                        'c_percent': kcs.c_percent,
                        'pb_percent': kcs.pb_percent,
                        'bb_percent': kcs.bb_percent,
                        'bleached_percent': kcs.bleached_percent,
                        'idb_percent': kcs.idb_percent,
                        'bits_percent': kcs.bits_percent,
                        'hulks_percent': kcs.hulks_percent,
                        'stone_percent': kcs.stone_percent,
                        'skin_out_percent': kcs.skin_out_percent,
                        'triage_percent': kcs.triage_percent,
                        'wet_bean_percent': kcs.wet_bean_percent,
                        'red_beans_percent': kcs.red_beans_percent,
                        'stinker_percent': kcs.stinker_percent,
                        'faded_percent': kcs.faded_percent,
                        'flat_percent': kcs.flat_percent,
                        'pb1_percent': kcs.pb1_percent,
                        'pb2_percent': kcs.pb2_percent,
                        'sleeve_6_up_percent': kcs.sleeve_6_up_percent,
                        'sleeve_5_5_up_percent': kcs.sleeve_5_5_up_percent,
                        'sleeve_5_5_down_percent': kcs.sleeve_5_5_down_percent,
                        'sleeve_5_down_percent': kcs.sleeve_5_down_percent,
                        'moisture_percent': kcs.moisture_percent,
                    })
    
    stack_id = fields.Many2one('stock.lot',string="Stack No.")
    picking_id = fields.Many2one('stock.picking',string="Gip")
    date = fields.Date(string='Date')
    zone_id = fields.Many2one('stock.zone',string='Zone', related='stack_id.zone_id', store=True)

    net_qty = fields.Float(compute='compute_qc', store=True, string ="Net Weight")
    real_qty = fields.Float(compute='compute_qc', store=True, string ="Real Weight")

    product_id = fields.Many2one('product.product',string="Product.",related='stack_id.product_id', store=True)
    categ_id = fields.Many2one('product.category', string='Category',related='stack_id.product_id.categ_id', store=True)
    bag_no = fields.Float(string='Bag No', compute='compute_qc', store=True)
    packing_id = fields.Many2one('ned.packing', string='Packing',compute='compute_qc')

    mc = fields.Float(compute='compute_qc', store=True, string='Mc')
    fm = fields.Float(compute='compute_qc', store=True, string='Fm')
    black = fields.Float(compute='compute_qc', store=True, string='Black')
    broken = fields.Float(compute='compute_qc', store=True, string='Broken')
    brown = fields.Float(compute='compute_qc', store=True, string='Brown')
    mold = fields.Float(compute='compute_qc', store=True, string='Mold')
    cherry = fields.Float(compute='compute_qc' ,store=True, string='Cherry')
    excelsa = fields.Float(compute='compute_qc' ,store=True, string='Excelsa')
    screen20 = fields.Float(compute='compute_qc', string =">20%", store=True)
    screen19 = fields.Float(compute='compute_qc', string =">19%", store=True)
    screen18 = fields.Float(compute='compute_qc', string =">18%", store=True)
    screen16 = fields.Float(compute='compute_qc', string =">16%", store=True)
    screen13 = fields.Float(compute='compute_qc', string =">13%", store=True)
    screen12 = fields.Float(compute='compute_qc', string ="<12%", store=True)
    greatersc12 = fields.Float(compute='compute_qc', string =">12%", store=True)
    burn = fields.Float(compute='compute_qc', string ="Burn", store=True)
    eaten = fields.Float(compute='compute_qc', string ="Eaten", store=True)
    immature = fields.Float(compute='compute_qc', string ="Immature", store=True)
    state = fields.Selection(related='picking_id.state', string='State')
    batch_id = fields.Many2one('batch.report', string="Outputs")
    
    stone_count = fields.Float(compute='compute_qc', string='Stone Count', store=True)
    stick_count = fields.Float(compute='compute_qc', string='Stick Count', store=True)

class BatchReportInstore(models.Model):
    _name = "batch.report.instore"
    
    stack_id = fields.Many2one('stock.lot',string="Stack No.")
    date = fields.Date(string='Date')
    net_qty = fields.Float(string ="Net Qty")
    
    product_id = fields.Many2one('product.product',string="Product.",related='stack_id.product_id', store=True)
    mc = fields.Float(related='stack_id.mc',store=True, string='Mc')
    fm = fields.Float(related='stack_id.fm',store=True,string='Fm')
    black = fields.Float(related='stack_id.black', string='Black',store=True)
    broken = fields.Float(related='stack_id.broken',string='Broken',store=True)
    brown = fields.Float(related='stack_id.brown',string='Brown',store=True)
    mold = fields.Float(related='stack_id.mold' ,string='Mold',store=True)
    cherry = fields.Float(related='stack_id.cherry' ,string='Cherry',store=True)
    excelsa = fields.Float(compute='stack_id.excelsa' ,store=True, string='Excelsa')
    screen20 = fields.Float(related='stack_id.screen20', string =">20%" ,store=True)
    screen19 = fields.Float(related='stack_id.screen19', string =">19%" ,store=True)
    screen18 = fields.Float(related='stack_id.screen18', string =">18%" ,store=True)
    screen16 = fields.Float(related='stack_id.screen16',string =">16%" ,store=True)
    screen13 = fields.Float(related='stack_id.screen13',string =">13%" ,store=True)
    screen12 = fields.Float(related='stack_id.screen12',string ="<12%",store=True)
    greatersc12 = fields.Float(related='stack_id.greatersc12', string =">12%", store=True)
    burn = fields.Float(related='stack_id.burn', string ="Burn", store=True)
    eaten = fields.Float(related='stack_id.eaten', string ="Eaten", store=True)
    immature = fields.Float(related='stack_id.immature', string ="Immature", store=True)
    batch_id = fields.Many2one('batch.report',string="Batch")
    production_id = fields.Many2one('mrp.production',related='batch_id.production_id',string="Batch")

    outturn_percent = fields.Float(string='Outturn%', related='stack_id.outturn_percent', store=True, digits=(12, 2))
    aaa_percent = fields.Float(string="AAA%", related='stack_id.aaa_percent', store=True, )
    aa_percent = fields.Float(string="AA%", related='stack_id.aa_percent', store=True, )
    a_percent = fields.Float(string="A%", related='stack_id.a_percent', store=True, )
    b_percent = fields.Float(string="B%", related='stack_id.b_percent', store=True, )
    c_percent = fields.Float(string="C%", related='stack_id.c_percent', store=True, )
    pb_percent = fields.Float(string="PB%", related='stack_id.pb_percent', store=True, )
    bb_percent = fields.Float(string="BB%", related='stack_id.bb_percent', store=True, )
    bleached_percent = fields.Float(string="Bleached%", related='stack_id.bleached_percent', store=True, )
    idb_percent = fields.Float(string="IDB%", related='stack_id.idb_percent', store=True, )
    bits_percent = fields.Float(string="Bits%", related='stack_id.bits_percent', store=True, )
    hulks_percent = fields.Float(string="Husk%", related='stack_id.hulks_percent', store=True, )
    stone_percent = fields.Float(string="Stone%", related='stack_id.stone_percent', store=True, )
    skin_out_percent = fields.Float(string='Skin Out%', related='stack_id.skin_out_percent', store=True, )
    triage_percent = fields.Float(string='Triage%', related='stack_id.triage_percent', store=True, )
    wet_bean_percent = fields.Float(string='Wet Beans%', related='stack_id.wet_bean_percent', store=True, )
    red_beans_percent = fields.Float(string='Red Beans%', related='stack_id.red_beans_percent', store=True, )
    stinker_percent = fields.Float(string='Stinker%', related='stack_id.stinker_percent', store=True, )
    faded_percent = fields.Float(string='Faded%', related='stack_id.faded_percent', store=True, )
    flat_percent = fields.Float(string='Flat%', related='stack_id.flat_percent', store=True, )
    pb1_percent = fields.Float(string='PB1%', related='stack_id.pb1_percent', store=True, )
    pb2_percent = fields.Float(string='PB2%', related='stack_id.pb2_percent', store=True, )
    sleeve_6_up_percent = fields.Float(string='6↑ %', related='stack_id.sleeve_6_up_percent', store=True, )
    sleeve_5_5_up_percent = fields.Float(string='5.5↑ %', related='stack_id.sleeve_5_5_up_percent', store=True, )
    sleeve_5_5_down_percent = fields.Float(string='5.5↓%', related='stack_id.sleeve_5_5_down_percent', store=True, )
    sleeve_5_down_percent = fields.Float(string='5↓ %', related='stack_id.sleeve_5_down_percent', store=True, )

    sleeve_5_up_percent = fields.Float(string='5↑ %', compute='compute_qc', store=True)
    unhulled_percent = fields.Float(string='Unhulled %', compute='compute_qc', store=True)
    remaining_coffee_percent = fields.Float(string='Remaining Coffee %', compute='compute_qc', store=True)
    blacks_percent = fields.Float(string='Blacks %', compute='compute_qc', store=True)
    half_monsoon_percent = fields.Float(string='Half Monsoon %', compute='compute_qc', store=True)
    good_beans_percent = fields.Float(string='Good Beans %', compute='compute_qc', store=True)

    moisture_percent = fields.Float(string='Moisture%', digits=(12, 2), related='stack_id.moisture_percent', store=True, )
    
    
    
class MrpProduction(models.Model):
    _inherit = 'mrp.production'
    
    # name = fields.Char('Reference', size=256, required=True, readonly=False, copy=False)
    # 
    # def action_done(self):
    #     res = super(MrpProduction, self).action_done()
    #     for this in self:
    #         bactch_report_ids = self.env['batch.report'].search([('production_id','=',this.id)])
    #         if bactch_report_ids:
    #             bactch_report_ids.load_data()
    #         else:
    #             bactch = self.env['batch.report'].create({'production_id':this.id})
    #             bactch.load_data()
    #     return res