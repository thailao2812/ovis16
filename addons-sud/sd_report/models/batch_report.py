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
                'sd_report.batch_report').report_action(self)
                
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
            print(sql)
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
                        sum(net_qty) total_in_qty,
                        sum(real_qty) total_real_qty,
                        sum(bag_no) total_bag
                    FROM batch_report_input
                    WHERE batch_id = %s
                    '''%(this.id)
                print(sql)
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
                        'total_bag': line['total_bag']
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
                        sum(net_qty) total_instore_qty
                        
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
                        sum(net_qty) total_out_qty
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

class BatchReportInput(models.Model):
    _name = "batch.report.input"

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