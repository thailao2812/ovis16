# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from datetime import datetime

    
    
class StockLot(models.Model):
    _inherit = "stock.lot"
    _order = 'id desc, create_date desc'
    
    
        # #Err Kiet
    qc_line_ids = fields.One2many('qc.stack.line', 'wr_id', string='QC Lines')
    
    
    def compute_qty(self):
        self._get_remaining_qty()
        self._compute_qc()
    
    # Da copy ben ned_kcs_vn
    @api.depends('move_line_ids', 
                 'move_line_ids.picking_id.state_kcs',
                 'move_line_ids.picking_id.state', 
                 'move_line_ids.picking_id.kcs_line',
                 'move_line_ids.init_qty')
    def _compute_qc(self):
        for this in self:
            if this.qc_line_ids:
                line_info = this.qc_line_ids[0]
                this.write({
                    'mc': line_info.mc and line_info.mc or '',
                    'fm': line_info.fm and line_info.fm or '',
                    'black': line_info.black and line_info.black or '',
                    'broken': line_info.broken and line_info.broken or '',
                    'screen13': line_info.screen13 and line_info.screen13 or '',
                    'screen16': line_info.screen16 and line_info.screen16 or '',
                    'screen18': line_info.screen18 and line_info.screen18 or '',
                })
            
            stick_count = stone_count = mc = immature = eaten = burned = belowsc12 = greatersc12 = screen13 = screen14 = screen15 = screen16 = screen17 = screen18 = 0.0
            screen19 = screen20 = excelsa = cherry = mold = fm = black = brown = broken = 0.0
            maize_yn = ''
            gip_net = gip_basis = gdn_basis = gdn_net = net_qty = basis_qty = 0.0
            packing_id = districts_id = production_id = False
            ligh_burnded_bean =0
            sampler = contract_no = remarks = ''
            count = 0
            net_qty = 0.0
            for line in this.move_line_ids:
                if line.picking_id.picking_type_id.code in ('production_in', 'transfer_in', 'incoming','phys_adj') and line.location_id.usage !='internal':
                    if line.state != 'done':
                        continue

                    for kcs in line.picking_id.kcs_line.filtered(lambda x: x.state == 'approved'):
                        if kcs.stack_id.id == this.id:
                            mc += kcs.mc * line.init_qty or 0.0
                            fm += kcs.fm * line.init_qty or 0.0
                            black += kcs.black * line.init_qty or 0.0
                            broken += kcs.broken * line.init_qty or 0.0
                            brown += kcs.brown * line.init_qty or 0.0
                            mold += kcs.mold * line.init_qty or 0.0
                            cherry += kcs.cherry * line.init_qty or 0.0
                            excelsa += kcs.excelsa * line.init_qty or 0.0
                            screen20 += kcs.screen20 * line.init_qty or 0.0
                            screen19 += kcs.screen19 * line.init_qty or 0.0
                            screen18 += kcs.screen18 * line.init_qty or 0.0
                            screen17 += kcs.screen17 * line.init_qty or 0.0
                            screen16 += kcs.screen16 * line.init_qty or 0.0
                            screen15 += kcs.screen15 * line.init_qty or 0.0
                            screen14 += kcs.screen14 * line.init_qty or 0.0
                            screen13 += kcs.screen13 * line.init_qty or 0.0
                            greatersc12 += kcs.greatersc12 * line.init_qty or 0.0
                            belowsc12 += kcs.belowsc12 * line.init_qty or 0.0
                            burned += kcs.burned * line.init_qty or 0.0
                            eaten += kcs.eaten * line.init_qty or 0.0
                            ligh_burnded_bean += kcs.ligh_burnded_bean * line.init_qty or 0.0
                        
                            immature += kcs.immature * line.init_qty or 0.0
                            
                            stick_count = kcs.stick_count
                            stone_count = kcs.stone_count
                            maize_yn = kcs.maize_yn
                            sampler = kcs.sampler
                            count += line.init_qty

                            packing_id = line.picking_id.packing_id and line.picking_id.packing_id.id

                    net_qty += line.init_qty
                    basis_qty += line.qty_done


                    if line.picking_id.note:
                        remarks += line.picking_id.note + ', '

                    if line.picking_id.contract_no:
                        contract_no += line.picking_id.contract_no + ', '

                    if line.picking_id.districts_id:
                        districts_id = line.picking_id.districts_id.id

                    if line.picking_id.production_id:
                        production_id = line.picking_id.production_id.id

                if line.picking_id.picking_type_id.code in ('outgoing', 'transfer_out') and line.state == 'done':
                    gdn_basis += line.qty_done
                    gdn_net += line.init_qty

                if line.picking_id.picking_type_id.code == 'production_out' and line.state == 'done':
                    gip_net += line.init_qty
                    gip_basis += line.qty_done

            this.update({'mc': count != 0 and mc / count or 0.0, 
                         'cherry': count != 0 and cherry / count or 0.0, 
                         'fm': count != 0 and fm / count or 0.0, 
                         'black': count != 0 and black / count or 0.0,
                         'broken': count != 0 and broken / count or 0.0, 
                         'screen20': count != 0 and screen20 / count or 0.0,
                         'brown': count != 0 and brown / count or 0.0, 
                         'mold': count != 0 and mold / count or 0.0,
                         'cherry': count != 0 and cherry / count or 0.0,
                         'excelsa': count != 0 and excelsa / count or 0.0, 
                         'screen19': count != 0 and  screen19 / count or 0.0, 
                         'screen18': count != 0 and screen18 / count or 0.0,
                         'screen17': count != 0 and screen17 / count or 0.0,
                         'screen16': count != 0 and screen16 / count or 0.0,
                         'screen15': count != 0 and screen15 / count or 0.0, 
                         'screen14': count != 0 and screen14 / count or 0.0,
                         'screen13': count != 0 and screen13 / count or 0.0, 
                         'screen12': count != 0 and belowsc12 / count or 0.0, 
                         'greatersc12': count != 0 and greatersc12 / count or 0.0,
                         'burn': count != 0 and burned / count or 0.0,
                         'eaten': count != 0 and eaten / count or 0.0,
                         'immature': count != 0 and immature / count or 0.0, 
                        'ligh_burnded_bean': count != 0 and ligh_burnded_bean / count or 0.0,  
                         'stick_count': stick_count, 
                         'stone_count': stone_count,
                         'maize': maize_yn, 
                         
                         'packing_id': packing_id, 
                         'net_qty': net_qty, 
                         'basis_qty': basis_qty, 
                         'remarks': remarks,
                         'sampler': sampler,
                         'gdn_basis': gdn_basis, 
                         'gdn_net': gdn_net, 
                         'gip_net': gip_net, 
                         'gip_basis': gip_basis,
                         'production_id': production_id, 
                         'districts_id': districts_id})
                
                
    
    production_id = fields.Many2one('mrp.production',string="Production",compute='_compute_qc',store=True)
    x_certificate_id = fields.Many2one(related='move_line_ids.picking_id.certificate_id', string='Certificate')

    mc = fields.Float(string="MC",compute='_compute_qc',group_operator="avg", digits=(12, 2),store=True)
    fm = fields.Float(compute='_compute_qc',string="Fm",group_operator="avg",  digits=(12, 2),store=True)
    black = fields.Float(compute='_compute_qc',string="Black",group_operator="avg",  digits=(12, 2),store=True)
    broken = fields.Float(compute='_compute_qc',string="Broken", group_operator="avg", digits=(12, 2),store=True)
    brown = fields.Float(compute='_compute_qc',string="Brown", group_operator="avg", digits=(12, 2),store=True) 
    mold = fields.Float(compute='_compute_qc',string="Mold", group_operator="avg", digits=(12, 2),store=True) 
    immature = fields.Float(compute='_compute_qc',string="immature",group_operator="avg",  digits=(12, 2),store=True)
     
    burn = fields.Float(compute='_compute_qc',string="Burn", group_operator="avg",  digits=(12, 2),store=True) 
    eaten = fields.Float(compute='_compute_qc',string="Insect", group_operator="avg", digits=(12, 2),store=True) 
    cherry = fields.Float(compute='_compute_qc',string="Cherry",group_operator="avg",  digits=(12, 2),store=True) 
    maize = fields.Char(string="Maize") 
    sampler = fields.Char(string="Sampler") 
    stone_count = fields.Float(string="Stone",compute='_compute_qc',group_operator="avg",  store=True)
    stick_count = fields.Float(string="Stick",compute='_compute_qc',group_operator="avg",  store=True) 
    screen20 = fields.Float(compute='_compute_qc',string="Screen20",group_operator="avg",   digits=(12, 2),store=True) 
    screen19 = fields.Float(compute='_compute_qc',string="Screen19",group_operator="avg",   digits=(12, 2),store=True) 
    screen18 = fields.Float(compute='_compute_qc',string="Screen18",group_operator="avg",   digits=(12, 2),store=True)
    screen17 = fields.Float(compute='_compute_qc',string="Screen17",group_operator="avg",   digits=(12, 2),store=True)
    screen16 = fields.Float(compute='_compute_qc',string="Screen16",group_operator="avg",   digits=(12, 2),store=True) 
    screen15 = fields.Float(compute='_compute_qc',string="Screen15",group_operator="avg",   digits=(12, 2),store=True)
    screen14 = fields.Float(compute='_compute_qc',string="Screen14",group_operator="avg",   digits=(12, 2),store=True)
    screen13 = fields.Float(compute='_compute_qc',string="Screen13",group_operator="avg",   digits=(12, 2),store=True)
    greatersc12 = fields.Float(compute='_compute_qc',string="Screen12",group_operator="avg",   digits=(12, 2),store=True) 
    screen12 = fields.Float(compute='_compute_qc',string="Below Screen12",group_operator="avg",   digits=(12, 2),store=True) 
    excelsa = fields.Float(compute='_compute_qc',string="Excelsa",group_operator="avg",  digits=(12, 2),store=True) 
    
    ligh_burnded_bean = fields.Float(compute='_compute_qc',string="Ligh Burnded Bean_%",group_operator="avg",   digits=(12, 2),store=True)
    
    packing_id = fields.Many2one('ned.packing',string="Packing",compute='_compute_qc',store=True)    
    
    net_qty = fields.Float(compute='_compute_qc',string="NET Qty",  digits=(12, 0),store=True) 
    basis_qty = fields.Float(compute='_compute_qc',string="Basis Qty",  digits=(12, 0),store=True) 
    remarks = fields.Char(string="Remarks",compute='_compute_qc',store=True)
    remarks_note = fields.Char(string="Remark Note")
    gdn_basis = fields.Float(compute='_compute_qc',string="Gdn Basis Qty",  digits=(12, 0),store=True) 
    gdn_net = fields.Float(compute='_compute_qc',string="Gdn Net Qty",  digits=(12, 0),store=True) 
    
    gip_net = fields.Float(compute='_compute_qc',string="Gip Net Qty",  digits=(12, 0),store=True) 
    gip_basis = fields.Float(compute='_compute_qc',string="Gip Basis Qty",  digits=(12, 0),store=True) 
    contract_no = fields.Char(string="Contract No",compute='_compute_qc',store=True)
    districts_id = fields.Many2one('res.district',compute='_compute_qc', string='Source', store=True)
    packing_id = fields.Many2one('ned.packing',string="Packing",compute='_compute_qc',store=True)    
    
    
    
    
    
    
