# -*- coding: utf-8 -*-
import time
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError


class wizard_stock_move(models.TransientModel):
    _name = "wizard.stock.move"
    
    wizard_id = fields.Many2one('wizard.stock.picking', 'Wizard Stock Picking', ondelete='cascade')
    result_id = fields.Many2one("mrp.operation.result", "Result")
    product_id = fields.Many2one("product.product", "Product")
    product_qty = fields.Float("Qty")
    product_uom = fields.Many2one("uom.uom","UoM")
    

class wizard_stock_picking(models.TransientModel):
    _name = "wizard.stock.picking"
    
    bag_qty = fields.Float(string="Bag Qty",digits=(12, 0))
    real_mc = fields.Float(string="Real MC",digits=(12, 2))
    real_weight = fields.Float(string="Net Weight.",digits=(12, 0))
    stack_empty = fields.Boolean('Stack empty', default = False)
    
    date = fields.Date(string="Scheduled Date")
    production_id = fields.Many2one("mrp.production", "Production")
    picking_type_id = fields.Many2one("stock.picking.type", "Picking Type")
    location_id = fields.Many2one("stock.location", "Source Location Zone")
    location_dest_id = fields.Many2one("stock.location", "Destination Location Zone")
    move_lines = fields.One2many("wizard.stock.move", "wizard_id", "Move Lines")
    product_id = fields.Many2one("product.product", "Product")
    product_qty = fields.Float(string="Product Qty",digits=(12, 0))
    basis_qty = fields.Float(string="basis_qty",digits=(12, 0))
    stack_id = fields.Many2one("stock.lot", "Stack")
    request_materials_id = fields.Many2one("request.materials", "Request Materials")
    warehouse_id = fields.Many2one("stock.warehouse", "Warehouse")
    
    def prepare_stock_move_line(self, picking):
        this = self
        product_uom_qty = this.product_qty - (this.product_qty * abs(this.stack_id.avg_deduction/100)) or 0.0
        val ={
                'picking_id': picking.id or False, 
                # 'name': name, 
                'product_uom_id': this.product_id.uom_id.id or False,
                # 'init_qty':this.real_weight or 0.0, 
                'init_qty':this.product_qty or 0.0, 
                'qty_done': product_uom_qty or 0.0, 
                'reserved_uom_qty':product_uom_qty or 0.0,
                'price_unit': 0.0,
                'picking_type_id': picking.picking_type_id.id or False,
                'location_id': picking.location_id.id or False,
                # 'date_expected': self.date or False, 'partner_id': False,
                'location_dest_id': picking.location_dest_id.id or False,
                # 'type': new_id.picking_type_id.code or False, 
                # 'scrapped': False, 
                'company_id': self.env.user.company_id.id, 
                'zone_id': this.stack_id.zone_id.id or False, 
                'product_id': this.product_id.id or False,
                'date': picking.date_done or False, 
                'currency_id': False,
                'state':'draft', 
                'warehouse_id': picking.warehouse_id.id or False,
                'lot_id':this.stack_id.id,
                'production_id': this.production_id.id or False,
                'packing_id':this.stack_id and this.stack_id.packing_id and this.stack_id.packing_id.id or False,
                'bag_no':this.bag_qty   ,
            }
        return val
    
    #Nghiêp vụ xuất kho
    def prepare_stock_picking(self):
        active_id = self._context.get('active_ids')
        result_obj = self.env['request.materials.line'].browse(active_id)
        warehouse_id = result_obj.request_id.warehouse_id or self.env['stock.warehouse'].search([('company_id', '=', self.env.user.company_id.id)], limit=1)
        
        location_id = False
        if not result_obj.stack_id:
            raise UserError('Stack/Lot cannot be empty')
        if not warehouse_id:
            raise UserError('Warehouse cannot be empty')
        if result_obj and result_obj.stack_id:
            location_id =  warehouse_id.wh_raw_material_loc_id
        crop_id = self.env['ned.crop'].search([('state', '=', 'current')], limit=1)
        
        val = {
           'name': '/', 
           'picking_type_id': warehouse_id.production_out_type_id.id, 
           'date_done':self.date, 
           'partner_id': False, 
           'crop_id':crop_id.id,
           #'picking_type_code': warehouse_id.production_out_type_id.code or False,
           'location_id': location_id and location_id.id or False, 
           'production_id': self.production_id.id or False,  
           'location_dest_id': warehouse_id.production_out_type_id.default_location_dest_id.id or False,
           'request_materials_id':self.request_materials_id.id,
           'warehouse_id':warehouse_id.id,
           'state':'draft',
           }  
        return val
        
    
    def button_create_picking(self):
        for this in self:
            active_id = self._context.get('active_ids')
            result_obj = self.env['request.materials.line'].browse(active_id)
#             if this.state =='cancel':
#                 raise UserError(u'Request Have been Canceled')
            if not result_obj.request_id.production_id:
                raise UserError(_('Please input Manufacturing Order before GIP goods into production'))
            
            if result_obj.request_id.production_id.state =='done':
                raise UserError(_('Manufacturing Order %s is Done, Cannot GIP anymore into production') %(result_obj.request_id.production_id.name))
            
            if this.product_qty > 0 > this.bag_qty:
                raise UserError(_('Number of bag cannot < 0'))
        
        
            if this.product_qty > result_obj.product_qty -result_obj.basis_qty:
                raise UserError(u'Request Qty is over')
            
            #Kiet Create Picking
            new_id = self.env['stock.picking'].create(self.prepare_stock_picking())
            move_id = self.env['stock.move.line'].create(self.prepare_stock_move_line(new_id))
            
            new_id.load_qc_gip()
            # done cho trường hợp là stack là hopper
            move_line_hopper = new_id.move_line_ids_without_package.filtered(lambda r: r.zone_id.hopper == True)
            new_id.button_qc_assigned()
            if move_line_hopper:
                #Kiet dim odoo gốc new_id.button_validate()
                new_id.btt_approved()
                
                # new_id.button_validate()
                new_id.button_sd_validate()
            #Kiet coi phải hàng hoper không, nếu co` hopper thì lây chất lượng bỏ wa
                    
            result_obj = self.env['request.materials.line'].browse(active_id)
            result_obj.write({'picking_ids': [(4, new_id.id)]})
            
            #Kiet nếu nó là zone hopper thì cho done, ko để yên
            
            
            result_obj = self.env['request.materials.line'].browse(active_id)
            result_obj.stack_empty = this.stack_empty
            if result_obj.product_qty == result_obj.basis_qty:
                result_obj.request_id.state = 'done'
            
        return True
    
    def button_create_picking_consumable(self):
        for this in self:
            active_id = self._context.get('active_ids')
            result_obj = self.env['request.materials.line'].browse(active_id)
#             if this.state =='cancel':
#                 raise UserError(u'Request Have been Canceled')
            if this.product_qty > result_obj.product_qty -result_obj.basis_qty:
                raise UserError(u'Request Qty is over')
            result_obj = self.env['request.materials.line'].browse(active_id)
            company = self.env.user.company_id.id or False
            warehouse_id = self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1)
            var = {
               'real_mc':this.real_mc,
               'real_weight':this.real_weight,
               'name': '/', 
               'picking_type_id': self.picking_type_id.id, 
               'scheduled_date': self.date or False, 
               'date_done':self.date, 
               'partner_id': False, 
               'picking_type_code': self.picking_type_id.code or False,
               'location_id': self.location_id.id or False, 
               'production_id': self.production_id.id or False, 
               'location_dest_id': self.location_dest_id.id or False,
               'request_materials_id':this.request_materials_id.id,
               'state':'draft'
            }  
            
            new_id = self.env['stock.picking'].create(var)
            product_uom_qty =0.0
            if this.stack_id:
                product_uom_qty = round(this.product_qty - (this.product_qty * abs(this.stack_id.avg_deduction/100)),0)
            else:
                product_uom_qty = this.product_qty
                
            name = '[' + this.product_id.default_code + '] ' + this.product_id.name or '' 
            move_id = self.env['stock.move.line'].create({'picking_id': new_id.id or False, 
                'name': name, 
                'init_qty':this.real_weight or 0.0,
                'product_uom': this.product_id.uom_id.id or False,
                'product_uom_qty': product_uom_qty or 0.0, 
                'reserved_uom_qty':product_uom_qty or 0.0,
#                 'init_qty': this.product_qty or 0.0, 
                'price_unit': 0.0,
                'picking_type_id': self.picking_type_id.id or False,
                'location_id': self.location_id.id or False,
                'date_expected': self.date or False, 'partner_id': False,
                'location_dest_id': self.location_dest_id.id or False,
                'type': self.picking_type_id.code or False, 'scrapped': False, 
                'company_id': company, 
                'packing_id':this.stack_id and this.stack_id.packing_id and this.stack_id.packing_id.id or False,
                'zone_id': this.stack_id.zone_id.id or False, 
                'product_id': this.product_id.id or False,
                'date': self.date or False, 'currency_id': False,
                'state':'draft', 
                'warehouse_id': warehouse_id.id or False,
                'stack_id':this.stack_id.id,
                'bag_no':this.bag_qty
                
                })
            result_obj.write({'picking_ids': [(4, new_id.id)]})
            this.production_id.move_lines =[(4, move_id.id)]
            new_id.action_done()
                
            result_obj = self.env['request.materials.line'].browse(active_id)
            result_obj.stack_empty = this.stack_empty
            if result_obj.product_qty == result_obj.basis_qty:
                result_obj.request_id.state = 'done'
            
        return True
    
    @api.model
    def default_get(self, fields):
        res = {}
        for result_line_obj in self.env['request.materials.line'].browse(self._context.get('active_ids')):
            result = result_line_obj.request_id
            if result.type == 'consu':
                picking_type_id = result.warehouse_id.production_out_type_consu_id or False
            else:
                picking_type_id = result.warehouse_id.production_out_type_id or False
            
            if not picking_type_id:
                raise UserError('Picking Type is not set for GIP, please check again with your warehouse setting')
            
            if result.state =='cancel':
                raise UserError(u'Request state Cancel')
            
            res = {
                'picking_type_id': picking_type_id.id, 
                'date': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'production_id': result.production_id.id or False,
                'location_id': picking_type_id.default_location_src_id.id or False, 
                'product_qty':result_line_obj.product_qty -result_line_obj.basis_qty,
                'basis_qty':result_line_obj.basis_qty,
                'product_id':result_line_obj.product_id.id,
                'stack_id':result_line_obj.stack_id.id,
                'request_materials_id':result.id,
                'location_dest_id': picking_type_id.default_location_dest_id.id or False}
                 
        return res
    
    