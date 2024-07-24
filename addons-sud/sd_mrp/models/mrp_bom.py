# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from datetime import datetime
    
    
class MrpBoMExtra(models.Model):
    _inherit = 'mrp.bom'

    master_code_id = fields.Many2one("master.code", string="Master Code", )
    type_code = fields.Char(string="Type", related='master_code_id.type_code', store=True, readonly=True, )
    batch_code = fields.Char(string="Batch code", )
    remarks = fields.Text(string="Remarks", related="master_code_id.remarks", store=True, readonly=True, )
    
    product_tmpl_id = fields.Many2one('product.template', string='Product',required=False,  domain="[('type', 'in', ['product', 'consu'])]")
    
    
    last_revised = fields.Date('Last Revised')
    crop_id = fields.Many2one('ned.crop',string = 'Crop')
    grade_id = fields.Many2one('product.category', string='Grade')
    bom_stage_lines =  fields.One2many('mrp.bom.stage.line', 'bom_id', 'MRP')
    description = fields.Text('Description')
    detail = fields.Text('Detail')
    
    # type = fields.Selection([('normal', 'Main product'),('phantom', 'Kit'), ('no', 'No main product')], 'BoM Type', required=True, default='no')
    type = fields.Selection(selection_add=[('no','No main product')],
                            ondelete={'supplier': 'set default',
                                'normal': 'set default',
                                'phantom': 'set default',
                                'no': 'set default',},
                            string='BoM Type', required=True, default='no')
    
    
    def name_get(self):
        return [(bom.id, '%s' % (bom.code)) for bom in self]



    
    
    
    
    
    

