# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from datetime import datetime
    
class MrpProductionStage(models.Model):
    _name = 'mrp.production.stage'
    
    sequence = fields.Integer('Sequence', required=True)
    name = fields.Char('Name', size=120, required=True)
    code =  fields.Char('Code', size=20, required=True)
    
class MrpBomStageLine(models.Model):
    _name = 'mrp.bom.stage.line'
    
    product_qty = fields.Float('Product qty', default= 1.0)
    ot_hour = fields.Float('Number of OT Hours')
    
    bom_id = fields.Many2one('mrp.bom', 'BOM', ondelete='cascade')
    seq = fields.Integer('Sequence')
    name = fields.Char('Name', size=64, required=True)
    production_stage_id =fields.Many2one('mrp.production.stage', 'Production Stage', required=False)
    workcenter_id = fields.Many2one('mrp.workcenter', 'Work Center', required=False)
    cycle_nbr = fields.Float('Number of Cycles', required=False, default= 1.0)
    hour_nbr = fields.Float('Number of Hours', required=False, default= 1.0)
    bom_stage_material_line = fields.One2many('mrp.bom.stage.material.line', 'bom_stage_line_id', 'Materials')
    bom_stage_output_line = fields.One2many('mrp.bom.stage.output.line', 'bom_stage_line_id', 'Semi or Finished Goods')
    
    
class MrpBomStageMaterialLine(models.Model):
    _name = 'mrp.bom.stage.material.line'
    
    name = fields.Char('Description', size=128, required=True)
    product_qty = fields.Float('Product qty')
    product_id = fields.Many2one('product.product', 'Product', required=False)
    categ_id = fields.Many2one('product.category', 'Category')
    off_topic = fields.Float('O/T(%)')
    
    def _get_sequence(self):
        res = {}
        seq = 1
        for line in self:
            line.sequence += seq
    
    sequence =  fields.Integer(compute= '_get_sequence', string='Sequence')
    name = fields.Char('name', size=64, required=False)
    product_id = fields.Many2one('product.product', 'Product', required=True)
    product_qty = fields.Float('Qty', required=True, default= 1.0)
    product_uom = fields.Many2one('uom.uom', 'UoM', required=True)
    bom_stage_line_id =  fields.Many2one('mrp.bom.stage.line', 'BOM Stage', required=False, ondelete='cascade')
    type = fields.Selection([('prime', 'Prime Material'),('other', 'Other')], 'Type')
    

class MrpBomStageOutputLine(models.Model):
    _name = 'mrp.bom.stage.output.line'
    
    off_topic = fields.Float('O/T(%)',default = 0.0)
    product_qty = fields.Float('Product qty')
    categ_id = fields.Many2one('product.category', 'Category')
    
    def _get_sequence(self):
        res = {}
        seq = 1
        for line in self:
            line.sequence += seq
    
    sequence = fields.Integer(compute= '_get_sequence', string='Sequence')
    product_id =  fields.Many2one('product.product', 'Product', required=True)
    product_uom = fields.Many2one('uom.uom', 'UoM', required=True)
    product_qty = fields.Float('Qty', default = 1)
    bom_stage_line_id =  fields.Many2one('mrp.bom.stage.line', 'BOM Stage', required=False, ondelete='cascade')
    
    def onchange_product_id(self):
        res = {}
        if self.product_id:
            self.product_uom = self.product_id.uom_id.id
    
              
    



    
    
    
    
    
    

