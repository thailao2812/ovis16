# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from datetime import datetime

    
class LotKcs(models.Model):
    _name ="lot.kcs"
    _order = "id desc"
    
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('lot.kcs.seq') 
        return super(LotKcs, self).create(vals)
    
    name = fields.Char(string="Lot no")
    lot_date = fields.Date(string="Date")
    contract_id = fields.Many2one('s.contract',string="S Contract")
    #lot_quantity = fields.Float(string="Lot Quantity")
    mc = fields.Float(string="MC")
    cup_test = fields.Char(string="Cup Test")
    los_ids = fields.One2many('lot.stack.allocation', 'lot_id', string="Lot Allocation", readonly=True)
    product_id = fields.Many2one(related='contract_id.product_id',  string='Product',store=True)
    x_packing_id = fields.Many2one('ned.packing', related='contract_id.contract_line.packing_id', string='Packing')
    x_pod_id = fields.Many2one('delivery.place', related='nvs_id.port_of_discharge', string='Destination')
    x_bulk_density = fields.Char(string='Bulk Density', size=256)
    x_ex_warehouse_id = fields.Many2one('x_external.warehouse', string="Warehouse")
    file = fields.Binary(string='File')
    file_name = fields.Char(string='File Name')
    
    @api.depends('quantity','defects','los_ids','los_ids.quantity','los_ids.stack_id','los_ids.grp_id','state','los_ids.grp_id.state_kcs')
    def _compute_qc(self):
        for line in self:
            stick_count = stone_count = mc = immature = eaten = burned = greatersc12 = belowsc12 = screen13 = screen15 = screen14 = screen16 = screen17 = screen18 =  screen19 = screen20 = excelsa = cherry = mold = fm = black = brown = broken = 0.0
            count =0
            for lot in line.los_ids:
                mc += lot.stack_id.mc * lot.quantity or 0.0
                fm += lot.stack_id.fm * lot.quantity or 0.0
                black += lot.stack_id.black * lot.quantity or 0.0
                broken += lot.stack_id.broken * lot.quantity or 0.0
                brown +=  lot.stack_id.brown * lot.quantity or 0.0
                mold += lot.stack_id.mold * lot.quantity or 0.0
                cherry += lot.stack_id.cherry * lot.quantity or 0.0
                excelsa += lot.stack_id.excelsa * lot.quantity or 0.0
                screen20 += lot.stack_id.screen20 * lot.quantity or 0.0
                screen19 += lot.stack_id.screen19 * lot.quantity or 0.0
                screen18 += lot.stack_id.screen18 * lot.quantity or 0.0
                screen17 += lot.stack_id.screen17 * lot.quantity or 0.0
                screen16 += lot.stack_id.screen16 * lot.quantity or 0.0
                screen15 += lot.stack_id.screen15 * lot.quantity or 0.0
                screen14 += lot.stack_id.screen14 * lot.quantity or 0.0
                screen13 += lot.stack_id.screen13 * lot.quantity or 0.0
                greatersc12 += lot.stack_id.greatersc12 * lot.quantity or 0.0
                belowsc12 += lot.stack_id.screen12 * lot.quantity or 0.0
                burned += lot.stack_id.burn * lot.quantity or 0.0
                eaten += lot.stack_id.eaten * lot.quantity or 0.0
                immature += lot.stack_id.immature *  lot.quantity or 0.0
                stick_count = lot.stack_id.stick_count 
                stone_count = lot.stack_id.stone_count 
                count += lot.quantity
                
            line.mc = count and mc/count or 0.0
            line.fm = count and fm/count or 0.0
            line.black = count and black/count or 0.0
            line.broken = count and broken/count or 0.0
            line.brown = count and brown/count or 0.0
            line.mold = count and mold/count or 0.0
            line.cherry = count and cherry/count or 0.0
            line.excelsa = count and excelsa/count or 0.0
            line.screen20 = count and screen20/count or 0.0
            line.screen19 = count and screen19/count or 0.0
            line.screen18 = count and screen18/count or 0.0
            line.screen17 = count and screen17/count or 0.0
            line.screen16 = count and screen16/count or 0.0
            line.screen15 = count and screen15/count or 0.0
            line.screen14 = count and screen14/count or 0.0
            line.screen13 = count and screen13/count or 0.0
            line.greatersc12 = count and greatersc12/count or 0.0
            line.screen12 = count and belowsc12/count or 0.0
              
            line.burn = count and burned/count or 0.0
            line.eaten = count and eaten/count or 0.0
            line.immature = count and immature/count or 0.0
            line.stick_count = stick_count
            line.stone_count = stone_count
                
    mc = fields.Float(string="MC",compute='_compute_qc', digits=(12, 2),store=True)
    fm = fields.Float(compute='_compute_qc',string="Fm",  digits=(12, 2),store=True)
    black = fields.Float(compute='_compute_qc',string="Black",  digits=(12, 2),store=True)
    broken = fields.Float(compute='_compute_qc',string="Broken",  digits=(12, 2),store=True)
    brown = fields.Float(compute='_compute_qc',string="Brown",  digits=(12, 2),store=True) 
    mold = fields.Float(compute='_compute_qc',string="Mold",  digits=(12, 2),store=True) 
    immature = fields.Float(compute='_compute_qc',string="immature",  digits=(12, 2),store=True)
    
    burn = fields.Float(compute='_compute_qc',string="Burn",  digits=(12, 2),store=True) 
    eaten = fields.Float(compute='_compute_qc',string="Insect",  digits=(12, 2),store=True) 
    cherry = fields.Float(compute='_compute_qc',string="Cherry",  digits=(12, 2),store=True) 
    maize = fields.Char(string="Maize") 
    stone = fields.Char(string="Stone") 
    stick = fields.Char(string="Stick") 
    sampler = fields.Char(string="Sampler") 
    screen20 = fields.Float(compute='_compute_qc',string="Screen20",  digits=(12, 2),store=True) 
    screen19 = fields.Float(compute='_compute_qc',string="Screen19",  digits=(12, 2),store=True) 
    screen18 = fields.Float(compute='_compute_qc',string="Screen18",  digits=(12, 2),store=True)
    screen17 = fields.Float(compute='_compute_qc',string="Screen17",  digits=(12, 2),store=True)
    screen16 = fields.Float(compute='_compute_qc',string="Screen16",  digits=(12, 2),store=True)
    screen15 = fields.Float(compute='_compute_qc',string="Screen15",  digits=(12, 2),store=True)
    screen14 = fields.Float(compute='_compute_qc',string="Screen14",  digits=(12, 2),store=True)
    screen13 = fields.Float(compute='_compute_qc',string="Screen13",  digits=(12, 2),store=True) 
    greatersc12 = fields.Float(compute='_compute_qc',string="Screen12",  digits=(12, 2),store=True) 
    screen12 = fields.Float(compute='_compute_qc',string="Screen12",  digits=(12, 2),store=True) 
    excelsa = fields.Float(compute='_compute_qc',string="Excelsa",  digits=(12, 2),store=True) 
    stone_count = fields.Char(string="Stone",compute='_compute_qc', store=True) 
    stick_count = fields.Char(string="Stick Count", compute='_compute_qc', store = True)
    
    fixed_mc = fields.Float(string="MC", digits=(12, 2))
    fixed_fm = fields.Float(string="Fm", digits=(12, 2))
    fixed_black = fields.Float(string="Black", digits=(12, 2))
    fixed_broken = fields.Float(string="Broken", digits=(12, 2))
    fixed_brown = fields.Float(string="Brown", digits=(12, 2)) 
    fixed_mold = fields.Float(string="Mold", digits=(12, 2)) 
    fixed_immature = fields.Float(string="immature", digits=(12, 2))
    
    fixed_burn = fields.Float(string="Burn", digits=(12, 2)) 
    fixed_eaten = fields.Float(string="Insect", digits=(12, 2)) 
    fixed_cherry = fields.Float(string="Cherry", digits=(12, 2)) 
    fixed_screen20 = fields.Float(string="Screen20", digits=(12, 2)) 
    fixed_screen19 = fields.Float(string="Screen19", digits=(12, 2)) 
    fixed_screen18 = fields.Float(string="Screen18", digits=(12, 2))
    fixed_screen17 = fields.Float(string="Screen17", digits=(12, 2))
    fixed_screen16 = fields.Float(string="Screen16", digits=(12, 2))
    fixed_screen15 = fields.Float(string="Screen15", digits=(12, 2))
    fixed_screen14 = fields.Float(string="Screen14", digits=(12, 2))
    fixed_screen13 = fields.Float(string="Screen13", digits=(12, 2)) 
    fixed_greatersc12 = fields.Float(string="Screen12", digits=(12, 2)) 
    fixed_screen12 = fields.Float(string="Screen12", digits=(12, 2)) 
    fixed_excelsa = fields.Float(string="Excelsa", digits=(12, 2))
    fixed_mc_on_despatch = fields.Float(string="Mc On Despatch", digits=(12, 2),store=True) 
    fixed_defects = fields.Float(digits=(12, 2),store=True, string="Defects") 
    
    cuptaste = fields.Char(string="Cuptaste",readonly=True,store=False,related='los_ids.cuptaste', )
    supervisor = fields.Char(string="Supervisor")
    
    quantity = fields.Float(string="Quantity")
    delivery_id = fields.Many2one('delivery.order',string="Do no.")
    state = fields.Selection([('draft', 'Draft'), ('approve', 'Approve')], string="State", required=True, default="draft")
    grp_id = fields.Many2one('stock.picking',string="GRP", domain="[('production_id', '!=', False),('state', '=', 'done'),('picking_type_id.code', '=', 'production_in')]")
    stack_id = fields.Many2one('stock.lot', string="Stack", readonly=False,store=True)
    nvs_id = fields.Many2one('sale.contract', string="NVS - Nls", readonly=True, domain="[('scontract_id', '=', contract_id)]")
    partner_id = fields.Many2one('res.partner',related='nvs_id.partner_id', string="Customer", store=True)
    lot_ned = fields.Char(string="Lot Ned")
    
    @api.depends('los_ids','los_ids.mc_on_despatch','los_ids.defects')
    def _compute_mc_on_despatch(self):
        for order in self:
            defects = mc_on_despatch = 0
            count =0
            for line in order.los_ids:
                mc_on_despatch += line.mc_on_despatch
                defects += line.defects
                count +=1
            if count:
                order.mc_on_despatch = mc_on_despatch/count
                order.defects = defects/count
            else:
                order.mc_on_despatch =0.0
                order.defects=0
            
    mc_on_despatch = fields.Float(compute='_compute_mc_on_despatch',string="Mc On Despatch",  digits=(12, 2),store=True)
    defects = fields.Float(compute='_compute_mc_on_despatch', digits=(12, 2),store=True, string="Defects") 
    
    @api.depends('los_ids','los_ids.quantity')
    def _total_qty(self):
        for order in self:
            total_qty = 0
            for line in order.los_ids:
                total_qty += line.quantity
            order.lot_quantity = total_qty
            
    lot_quantity = fields.Float(compute='_total_qty', digits=(16, 0) , string='Lot Quantity',store=True)
    qty_scontract = fields.Float(related='contract_id.total_qty',  string='Qty SContract',store=True)
    
    def get_qc(self):
        for this in self:
            this.update({'fixed_mc': this.mc,
                        'fixed_mc_on_despatch': this.mc_on_despatch,
                        'fixed_fm': this.fm,
                        'fixed_black': this.black,
                        'fixed_broken': this.broken,
                        'fixed_brown': this.brown,
                        'fixed_mold': this.mold,
                        'fixed_cherry': this.cherry,
                        'fixed_screen20': this.screen20,
                        'fixed_screen19': this.screen19,
                        'fixed_screen18': this.screen18,
                        'fixed_screen17': this.screen17,
                        'fixed_screen16': this.screen16,
                        'fixed_screen15': this.screen15,
                        'fixed_screen14': this.screen14,
                        'fixed_screen13': this.screen13,
                        'fixed_greatersc12': this.greatersc12,
                        'fixed_screen12': this.screen12,
                        'fixed_burn': this.burn,
                        'fixed_eaten': this.eaten,
                        'fixed_excelsa': this.excelsa,
                        'fixed_defects': this.defects,
                        'fixed_immature': this.immature
                })
        return True
            
    lot_quantity = fields.Float(compute='_total_qty', digits=(16, 0) , string='Lot Quantity',store=True)
    qty_scontract = fields.Float(related='contract_id.total_qty',  string='Qty SContract',store=True)
    
    def btt_draft(self):
        for this in self:
            this.state = 'draft'
            
    def btt_confirm(self):
        for this in self:
            this.state = 'approve'
        