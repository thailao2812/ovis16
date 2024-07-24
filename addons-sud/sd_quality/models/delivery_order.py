# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from datetime import datetime
    
    
class DeliveryOrder(models.Model):
    _inherit = "delivery.order"
    
    #do_kcs = fields.One2many('do.kcs', 'do_id', string="DO KCS")
    
    
    @api.depends('fm','product_id','picking_id','picking_id.state')
    def _compute_qc(self):
        for line in self:
            if line.picking_id and line.product_id:
                immature = eaten = burned = belowsc12 = greatersc12 = screen13 = screen16 = screen18 = screen19 = screen20 = excelsa = cherry = mold = fm = black = brown = broken = 0.0
                count =0
                for move_line in line.picking_id.move_line_ids_without_package:
                    if move_line.product_id.id == line.product_id.id:
                          
                        for move in move_line.lot_id.move_line_ids:
                            if (move.location_id.usage != 'internal' and move.location_dest_id.usage == 'internal') != True:
                                continue
                            for kcs in move.picking_id.kcs_line:
                                fm += kcs.fm or 0.0
                                black += kcs.black or 0.0
                                broken += kcs.broken or 0.0
                                brown +=  kcs.brown or 0.0
                                mold += kcs.mold or 0.0
                                cherry += kcs.cherry or 0.0
                                excelsa += kcs.excelsa or 0.0
                                screen20 += kcs.screen20 or 0.0
                                screen19 += kcs.screen19 or 0.0
                                screen18 += kcs.screen18 or 0.0
                                screen16 += kcs.screen16 or 0.0
                                screen13 += kcs.screen13 or 0.0
                                greatersc12 += kcs.greatersc12 or 0.0
                                belowsc12 += kcs.belowsc12 or 0.0
                                burned += kcs.burned or 0.0
                                eaten += kcs.eaten or 0.0
                                immature += kcs.immature or 0.0
                                count +=1
                                  
                line.fm = count and fm/count or 0.0
                line.black = count and black/count or 0.0
                line.broken = count and black/count or 0.0
                line.brown = count and brown/count or 0.0
                line.mold = count and mold/count or 0.0
                line.cherry = count and cherry/count or 0.0
                line.excelsa = count and excelsa/count or 0.0
                line.screen20 = count and screen20/count or 0.0
                line.screen19 = count and screen19/count or 0.0
                line.screen18 = count and screen18/count or 0.0
                line.screen16 = count and screen16/count or 0.0
                line.screen13 = count and screen13/count or 0.0
                line.greatersc12 = count and greatersc12/count or 0.0
                line.screen12 = count and belowsc12/count or 0.0
                  
                line.burn = count and burned/count or 0.0
                line.eaten = count and eaten/count or 0.0
                line.immature = count and immature/count or 0.0
     
    lot_no = fields.Char(string="Lot No")      
#     date_tz = fields.Date(compute='_compute_date',string = "date", store=True)
#     day_tz = fields.Char(compute='_compute_date',string = "Month", store=True)
    
    mc = fields.Float(string="MC")
    fm = fields.Float(compute='_compute_qc',string="Fm",  digits=(12, 2),store=True)
    black = fields.Float(compute='_compute_qc',string="Black",  digits=(12, 2),store=True)
    broken = fields.Float(compute='_compute_qc',string="Broken",  digits=(12, 2),store=True)
    brown = fields.Float(compute='_compute_qc',string="Brown",  digits=(12, 2),store=True) 
    mold = fields.Float(compute='_compute_qc',string="Mold",  digits=(12, 2),store=True) 
    immature = fields.Float(compute='_compute_qc',string="immature",  digits=(12, 2),store=True)
    defects = fields.Float(string="Defects",  digits=(12, 2)) 
    burn = fields.Float(compute='_compute_qc',string="Burn",  digits=(12, 2),store=True) 
    eaten = fields.Float(compute='_compute_qc',string="Insect",  digits=(12, 2),store=True) 
    cherry = fields.Float(compute='_compute_qc',string="Cherry",  digits=(12, 2),store=True) 
    maize = fields.Float(string="Maize",  digits=(12, 2),store=True) 
    stone = fields.Float(string="Stone",  digits=(12, 2),store=True) 
    stick = fields.Float(string="Stick",  digits=(12, 2),store=True) 
    screen20 = fields.Float(compute='_compute_qc',string="Screen20",  digits=(12, 2),store=True) 
    screen19 = fields.Float(compute='_compute_qc',string="Screen19",  digits=(12, 2),store=True) 
    screen18 = fields.Float(compute='_compute_qc',string="Screen18",  digits=(12, 2),store=True) 
    screen16 = fields.Float(compute='_compute_qc',string="Screen16",  digits=(12, 2),store=True) 
    screen13 = fields.Float(compute='_compute_qc',string="Screen13",  digits=(12, 2),store=True) 
    greatersc12 = fields.Float(compute='_compute_qc',string="Screen12",  digits=(12, 2),store=True) 
    screen12 = fields.Float(compute='_compute_qc',string="Screen12",  digits=(12, 2),store=True) 
    excelsa =  fields.Float(compute='_compute_qc',string="Excelsa",  digits=(12, 2),store=True) 
    cuptaste = fields.Char(string="Cuptaste")
    supervisor = fields.Char(string="Supervisor")
    
    