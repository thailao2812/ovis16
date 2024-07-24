# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from odoo.tools import float_round
from odoo.exceptions import UserError, ValidationError


class RequestMaterials(models.Model):
    _name = "request.materials"
    _description = "Request Materials"
    _order = 'id desc'
    _inherit = ['mail.thread']
    
    name = fields.Char(string="Request")
    production_id = fields.Many2one('mrp.production', string='Manufacturing Orders', required=False)
    # pp_id = fields.Many2one('mrp.production', string='Manufacturing Orders', required=True)
    #related='production_id.warehouse_id',
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', readonly=False,store=True)
    request_date = fields.Date("Request Date",default=fields.Datetime.now)
    request_user_id = fields.Many2one('res.users', string='Request Users',
       readonly=True, states={'draft': [('readonly', False)]}, required=False,default=lambda self: self._uid)
    request_line = fields.One2many('request.materials.line', 'request_id', string='Request Lines', 
                       readonly=True, states={'draft': [('readonly', False)]}, copy=True)
    origin= fields.Char('Origin')
    notes = fields.Text(string='Notes')
    state = fields.Selection([('draft', 'New'),('scale','Scale'), ('approved', 'Approved'), ('done', 'Done'),('cancel','Canceled')], string='Status',
                             readonly=True, copy=False, index=True, default='draft')
    type = fields.Selection([('consu', 'Consumable'), ('mrp', 'Production')], string='Type',
                             default='mrp')
    
    def _total_qty(self):
        for order in self:
            total_qty = 0.0
            for line in order.request_line:
                total_qty += line.product_qty
            order.total_qty = total_qty
            
    total_qty = fields.Float(compute='_total_qty', digits=(16, 0) , string='Qty')
    
    def set_to_approved(self):
        for this in self:
            if this.state =='done':
                this.state ='approved'
                
            for line in this.request_line:
                for pick in line.picking_ids:
                    if pick.state != 'done':
                        pick.kcs_line.unlink()
                        for k in pick.move_line_ids_without_package:
                            k.qty_done = 0
                        
                        pick.action_cancel()
                        pick.unlink()
                        
    
    def unlink(self):
        for record in self:
            if record.state not in ('draft', 'cancel'):
                raise UserError(_('You cannot delete is not draft or cancelled.'))
        return super(RequestMaterials, self).unlink()
    
    @api.model
    def create(self, vals):
        if vals.get('type',False) == 'consu':
            vals['name'] = self.env['ir.sequence'].next_by_code('request.materials.consu')
        else:
            vals['name'] = self.env['ir.sequence'].next_by_code('request.materials')
        result = super(RequestMaterials, self).create(vals)
        return result
    
    def write(self, vals):
        result = super(RequestMaterials, self).write(vals)
        return result
    
    def button_draft(self):
        for request in self:
            # if request.picking_id and request.picking_id.state !='draft':
            #     raise UserError(_("Picking (%s) was approved") % (request.picking_id.name))
            # request.picking_id.unlink()
            request.state = 'draft'
            
    def button_cancel(self):
        self.state = 'cancel'
    
    def button_done(self):
        list = ['bag_qty', 'real_mc', 'real_weight', 'stack_empty', 'date', 'picking_type_id', 'location_id', 
                'location_dest_id', 'product_qty']
        for i in self.request_line:
            if i.stack_id.zone_id.hopper == True:
                vals = self.env['wizard.stock.picking'].with_context(active_ids=[i.id]).default_get(list)
                vals['bag_qty'] = i.stack_id.bag_qty
                wizard_picking = self.env['wizard.stock.picking'].create(vals)
                wizard_picking.with_context(active_ids= [i.id]).button_create_picking()
        self.state = 'done'
                
class RequestMaterialsLine(models.Model):
    _name = "request.materials.line"
    _description = "Request Materials Line"
    
    @api.depends('picking_ids')
    def _basis_qty(self):
        for picking in self:
            basis_qty = 0.0
            for line in picking.picking_ids:
                if line.state in ('cancel'):
                    continue
                basis_qty +=line.total_init_qty 
            picking.basis_qty = basis_qty
            
    product_id = fields.Many2one('product.product', string='Product')
    product_uom = fields.Many2one('uom.uom', string='UoM')
    product_qty = fields.Float( string='Product Qty',digits=(12, 0), default = 0)
    request_id = fields.Many2one('request.materials', string='Request')
    picking_ids = fields.Many2many('stock.picking','picking_request_move_ref','picking_id','request_id','Picking', copy = False)
    basis_qty = fields.Float(compute='_basis_qty', string='Basis Qty',digits=(12, 0))
    state = fields.Selection([('approved', 'Approved'),('cancel','Canceled')], string='Status',
                             readonly=True, copy=False, index=True, default='approved')
    
    stack_id = fields.Many2one('stock.lot',string ='Stack', copy = False)
    stack_empty = fields.Boolean('Stack empty', default = False)
    
    # 
    bag_no = fields.Float(related ='stack_id.bag_qty', string ='Bag No', store= True)

    @api.depends('stack_id')
    def _get_balance_qty(self):
        for line in self:
            if line.stack_id:
                line.qty_stack = line.stack_id.init_qty or 0.0
            else:
                line.qty_stack = 0
            
    qty_stack = fields.Float(compute='_get_balance_qty',  string='Qty Stack', digits=(12, 0), store=True)
    
    def btt_cancel(self):
        self.state = 'cancel'
    
    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return {'domain': {'product_uom': []}}

        vals = {}
        domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}

        vals['product_uom'] = self.product_id.uom_id

        self.update(vals)
        return {'domain': domain}
    

class StockPicking(models.Model):
    _inherit = "stock.picking"
    
    request_materials_id = fields.Many2one('request.materials', string='Request Materials')