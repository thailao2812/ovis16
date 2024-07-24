# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from odoo.tools import float_round
import time
from datetime import timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import timedelta, datetime, date
import calendar

class WizardRequestMaterials(models.TransientModel):
    _name = "wizard.request.materials"
    
    production_id = fields.Many2one('mrp.production',string ='Manufacturing Orders')
    request_date = fields.Date(string='Date')
    warehouse_id = fields.Many2one('stock.warehouse',string ='Warehouse')
    request_line = fields.One2many('wizard.request.materials.line','request_id',string="Request Line")
    
    @api.model
    def default_get(self, fields):
        res = {}
        vars=[]
        active_id = self._context.get('active_id')
        if active_id:
            production_obj = self.env['mrp.production'].browse(active_id)
            res = {'production_id': active_id, 
                   'request_date': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                   'warehouse_id':production_obj.warehouse_id.id}
            for j in production_obj.bom_id.bom_stage_lines:
                for line in j.bom_stage_material_line:
                    vars.append((0, 0, {'product_id':line.product_id.id, 'product_uom':line.product_uom.id,'product_qty' :line.product_qty}))
            res.update({'request_line':vars})
        return res
    
    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return {'domain': {'product_uom': []}}
        vals = {}
        domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        vals['product_uom'] = self.product_id.uom_id
        self.update(vals)
        return {'domain': domain}
    
    
    def button_request(self):
        for this in self:
            if not this.request_line:
                raise UserError(_("Materials is not Null"))
            for line in this.request_line:
                if line.product_qty == 0:
                    raise UserError(_("Request Qty is not Null"))
            val ={
                    'warehouse_id':this.warehouse_id.id,
                    'production_id':this.production_id.id,
                    'origin':this.production_id.name,
                    'request_user_id':self.env.uid,
                    'state':'draft'
                }
            request_id = self.env['request.materials'].create(val)
            
            for line in this.request_line:
                vals ={
                    'product_id':line.product_id.id,
                    'product_uom':line.product_uom.id,
                    'product_qty':line.product_qty or 0.0,
                    'request_id':request_id.id,
                    'stack_id':line.stack_id.id
                    }
                self.env['request.materials.line'].create(vals)
            request_id.state = 'approved'
                

class wizard_request_materials_line(models.TransientModel):
    _name = "wizard.request.materials.line"

    request_id = fields.Many2one('wizard.request.materials',string ='Request')
    product_id = fields.Many2one('product.product',string ='Product')
    product_uom = fields.Many2one('uom.uom',string ='UoM')
    product_qty = fields.Float(string ='Qty',digits=(16, 0))
    
    
    @api.onchange('stack_id')
    def onchange_stack_id(self):
        if not self.stack_id:
            self.update({'product_qty': 0.0})
        else:
            self.update({'product_qty': self.stack_id.init_qty or 0.0})
        
    stack_id = fields.Many2one('stock.lot',string ='Stack')
    
    @api.onchange('product_id')
    def onchange_product(self):
        if not self.product_id:
            return
        else:
            self.product_uom = self.product_id.uom_id.id
        
    stack_id = fields.Many2one('stock.lot',string ='Stack')
    
    #product_qty = fields.Float(related='stack_id.remaining_qty',string ='Qty',digits=(16, 0))
    
