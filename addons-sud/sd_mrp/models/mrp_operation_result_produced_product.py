# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _, tools
import time
from datetime import timedelta
from odoo.exceptions import UserError, ValidationError


class MrpOperationResultProducedProduct(models.Model):
    _name = 'mrp.operation.result.produced.product'

    def unlink(self):
        if not self.env.user.user_has_groups('sd_mrp.group_delete_mrp_production_result'):
            raise UserError(_('You cannot delete records of this model!'))
        res = super(MrpOperationResultProducedProduct, self).unlink()
    
    
    state= fields.Selection([
        ('draft', 'Draft'),
        ('cancel', 'Cancelled'),
        ('done', 'Done'),
        ], 'Status', readonly=True, default='draft')
    
    
    def button_cancel(self):
        for i in self:
            if i.picking_id and (i.picking_id.state =='done' or i.picking_id.state_kcs !='draft'):
                error = "Không thể Cancel, Bởi vì QC đã Approved"
                raise UserError(_(error))
            else:
                i.picking_id.btt_reject()
                i.state ='cancel'
    
    
    product_id = fields.Many2one('product.product', 'Product', required=True)
    product_uom = fields.Many2one('uom.uom', 'UoM', required=True)
    notes = fields.Text('Notes')
    operation_result_id = fields.Many2one('mrp.operation.result', 'Operation Result', ondelete='cascade')
    
    
    
    qty_bags = fields.Float(digits=(12, 0) , string='Bags',)
    production_weight = fields.Float(digits=(12, 0) , string='Net Weight')
    si_id = fields.Many2one('shipping.instruction', 'SI')
    #erro kiet
    # stack_id = fields.Many2one('stock.product.lot',related='picking_id.stack_id', string='Stack',store=True)
    
    lot_id = fields.Many2one('stock.lot',related='picking_id.lot_id', string='Stack',store=True)
    
    production_id = fields.Many2one('mrp.production',related='operation_result_id.production_id', string='Production',store=True)
    start_date = fields.Datetime(related='operation_result_id.start_date',string='Start Date', store= True)
    end_date = fields.Datetime(related='operation_result_id.end_date',string='End Date' , store= True)
    
    product_qty =fields.Float('Product Qty',digits=(12, 0))
    pending_grn = fields.Char('Pending GRN')
    packing_id = fields.Many2one('ned.packing', string='Packing')
    qty_packing = fields.Float('Qty Packing')
    picking_id = fields.Many2one('stock.picking', string='From Processing')
    state_kcs =fields.Selection(related = 'picking_id.state_kcs', string='State Kcs', readonly=True)
    zone_id = fields.Many2one('stock.zone',string='Zone', required=False )
    notes = fields.Char(string="Note",size=128)
    kcs_notes =fields.Char(string="QC Note",size=128)
    
    
    
    @api.constrains('product_qty')
    def _check_qty(self):
        for produced in self:
            if produced.product_qty <= 0:
                return False
        return True
    
    
    
    
    @api.model
    def default_get(self, default_fields):
        prodlot_id = False
        res = super(MrpOperationResultProducedProduct, self).default_get(default_fields)
        # if self.context.get('default_operation_id',False):
        #     operation_id = context['default_operation_id']
        #     res.update({'default_operation_id': operation_id})
        return res
    
    @api.onchange('product_id')
    def onchange_product_id(self):
        product_uom = False
        if self.product_id:
            self.product_uom =  self.product_id.uom_id.id or False
        
    def create_kcs(self):
        produced = self
        produced.state = 'done'
        warehouse_obj = produced.operation_result_id.warehouse_id or produced.operation_result_id.production_id.warehouse_id
        result = produced.operation_result_id
        production_obj = produced.operation_result_id.production_id
        product_qty = production_weight = 0
        company_id = production_obj.company_id.id or False
        move = self.env['stock.move']
        move_line = self.env['stock.move.line']
        # operation_produce = self.env['mrp.production.workcenter.product.produce']
        # operation_consumed = self.env['mrp.production.workcenter.consumed.produce']
        if produced.picking_id:
            return
        # if produced.product_qty > 0 and produced.production_weight > 0: 
        if produced.product_qty > 0: 
         
            picking_type_id = warehouse_obj.production_in_type_id or False
             
            if not picking_type_id.default_location_src_id:
                error = "Production Locations  does not exist."
                raise UserError(_(error))
            location_id = picking_type_id.default_location_src_id
            
            if not picking_type_id.default_location_dest_id.id:
                error = "Location Destination does not exist."
                raise UserError(_(error))
            location_dest_id = picking_type_id.default_location_dest_id.id
             
         
            product_qty += produced.product_qty
            production_weight += produced.production_weight
            crop_id = self.env['ned.crop'].search([('state', '=', 'current')], limit=1)
            
            # name_seq =  picking_type_id.sequence_id.next_by_id()
            # if crop_id.short_name:
            #     crop = '-' + crop_id.short_name +'-'
            #     name_seq = name_seq.replace("-", crop, 1)
                
                
            # Kiệt: Create nhập kho Thành phẩm Thêm Picking để KCS Sucden
            var = {
                'crop_id':crop_id.id,
                'warehouse_id':warehouse_obj.id,
                'name': '/',
                'date_done': time.strftime('%Y-%m-%d %H:%M:%S') or False,
                'picking_type_id': picking_type_id.id,
                'partner_id': False,
                'date': fields.Datetime.now(),
                # 'date_sent': fields.Datetime.now(),
                'origin': produced.pending_grn or False,
                'location_dest_id': location_dest_id,
                'location_id': location_id.id,
                'state':'draft',
                'production_id':production_obj.id,
                # 'operation_id':result.operation_id.id,
                # 'result_id':result.id,
                'note':produced.notes
            }
            picking_id = self.env['stock.picking'].create(var)
            move_line.create({'picking_id': picking_id.id, 
                              # 'name': produced.product_id.name or '', 
                            'product_id': produced.product_id.id or False,
                            'product_uom_id': produced.product_uom.id or False, 
                            'init_qty':produced.product_qty or 0.0, 'weighbridge':produced.production_weight or 0.0, 
                            'qty_done': produced.product_qty or 0.0, 
                            #'price_unit': 0.0,
                            'picking_type_id': picking_type_id.id or False, 'location_id': location_id.id or False, 'production_id': production_obj.id,
                            'location_dest_id': location_dest_id or False, 
                            'date': time.strftime('%Y-%m-%d %H:%M:%S') or False, 
                            #'type': picking_type_id.code or False, 'result_id': result.id,
                            'zone_id':produced.zone_id and produced.zone_id.id or False,
                            'packing_id':produced.packing_id.id,
                            'bag_no':produced.qty_bags or 0.0,
                            'company_id': company_id, 'state':'draft', 
                            # 'scrapped': False, 
                            'warehouse_id': warehouse_obj.id or False,
                            #Lien kết vối lệnh sản xuất
                            'finished_id':production_obj.id,
                            })
            picking_id.button_qc_assigned()
            produced.picking_id = picking_id.id
             
        return


class MrpOperationResultConsumedProduct(models.Model):
    _name = 'mrp.operation.result.consumed.product'
    
    product_id = fields.Many2one('product.product', 'Product', required=True)
    product_qty = fields.Float('Product Quantity',  required=True)
    product_uom = fields.Many2one('uom.uom', 'UoM', required=True)
    operation_result_id = fields.Many2one('mrp.operation.result', 'Operation Result', ondelete='cascade')
    move_id =fields.Many2one('stock.move', 'Move Line', ondelete='cascade')
    picking_id =fields.Many2one('stock.picking', 'Picking', required=False)
    # date_consumed =fields.Datetime(related = 'picking_id.date_done', type='date', string='Date Consumed', readonly=True)

