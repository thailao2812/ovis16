# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
import time

class StockMoveLine(models.Model):
    _inherit = "stock.move.line"
    
    stack_id = fields.Many2one('stock.stack', string='Stack', ondelete='cascade', index=True, copy=False, 
                           domain="[('product_id', '=', product_id)]", tracking=True)
    zone_id = fields.Many2one('stock.zone', string='Zone', index=True, copy=False, ondelete='restrict', tracking=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', index=True, copy=False)
    price_unit = fields.Float(string='Price unit', index=True, copy=False)
    currency_id = fields.Many2one('res.currency', string="Currency")
    price_currency = fields.Float(string='Price Currency', index=True, copy=False)
    partner_id = fields.Many2one(related="picking_id.partner_id", string="Partner", store = True)
    picking_type_id = fields.Many2one(related ="picking_id.picking_type_id", string= 'Picking type', index=True, copy=False, store = True)
    entries_id = fields.Many2one('account.move',string="Entries")
    category_id = fields.Many2one('product.category', related='product_id.categ_id', store=True)
    
    # picking_type_code = fields.Selection(related="picking_id.picking_type_id.code", string="Picking Type Code", store = True)
    
    @api.constrains('init_qty')
    def _contrains_init_qty(self):
        for obj in self:
            if obj.init_qty <= 0 and obj.state and obj.state != 'draft':
                raise ValidationError(_('NET Qty> 0'))
        
    @api.constrains('bag_no', 'lot_id', 'state')
    def _contrains_bag_no(self):
        for obj in self:
            if obj.picking_id.picking_type_id.code not in ('material_in','material_out','phys_adj', 'outgoing') and obj.bag_no <= 0 and obj.state != 'draft':
                if obj.lot_id:
                    raise ValidationError(_('Bag Qty> 0'))
            if obj.picking_id.picking_type_id.code == 'outgoing':
                if obj.lot_id.bag_qty > 0 >= obj.bag_no and obj.state != 'draft':
                    raise ValidationError(_('Bag Qty> 0'))
    
    
    @api.onchange("bag_no")
    def onchange_bag_no(self):
        for move in self:
            values =  {'qty_done': move.init_qty or 0.0,'reserved_uom_qty':move.init_qty or 0.0}
            move.update(values)
        
    init_qty = fields.Float(string='Net Weight', digits=(12, 0), copy=True, tracking=True)
    
    #Kiet, chưa hiểu fields này
    #grp_id = fields.Many2one('stock.picking', string='GRP', index=True, copy=False, )
    weighbridge = fields.Float('Weigh Bridge',digits=(12, 0), required=True, default=0,)
    gross_weight = fields.Float(string='Gross Weight')
    # type = fields.Selection(selection_add=[('material_in','Material In'),('material_out','Material Out')])
    stack_empty = fields.Boolean('Stack empty', default = False, tracking=True)
    # picking_type_code = fields.Selection(related ='picking_type_id.code',string='Picking Type',store =True)
    
    first_weight = fields.Float(string="First Weight",digits=(12, 0), tracking=True)
    second_weight = fields.Float(string="Second Weight",digits=(12, 0), tracking=True)
    packing_id = fields.Many2one('ned.packing', string='Packing', tracking=True)
    bag_no = fields.Float(string="Bag nos.",digits=(12, 0), tracking=True)
    tare_weight = fields.Float(string="Tare Weight",digits=(12, 2), tracking=True)
    weight_scale_id = fields.Char(string='Weight Scale No.')
    
    @api.onchange('first_weight','second_weight','packing_id','bag_no','tare_weight')
    def onchange_weight(self):
        if not self.packing_id:
            tare_weight = 0.0
            net_weight = (self.first_weight or 0.0) - (self.second_weight or 0.0) - tare_weight
            if net_weight:
                self.update({'tare_weight':tare_weight,'init_qty':net_weight,'qty_done':net_weight})
        else:
            tare_weight = self.packing_id.tare_weight or 0.0
            tare_weight = round(self.bag_no * tare_weight,0)
            net_weight = (self.first_weight or 0.0) - (self.second_weight or 0.0) - tare_weight
            if net_weight:
                self.update({'tare_weight':tare_weight,'init_qty':net_weight, 'qty_done':net_weight})
                
    @api.onchange('init_qty')
    def onchange_init_qty(self):
        self.update({'qty_done':self.init_qty})
                
    
    def check_stack_empty(self):
        if self.stack_id:
            self.stack_empty = True
            msg = _("'%s' Check Stack Empty = True ") % (_(self.stack_id.name))
            self.picking_id.message_post(body=msg)
    
    def uncheck_stack_empty(self):
        if self.stack_id:
            self.stack_empty = False    
            msg = _("'%s' Check Stack Empty = False ") % (_(self.stack_id.name))
            self.picking_id.message_post(body=msg)
    
    @api.onchange('lot_id')
    def onchange_lot_id(self):
        if not self.lot_id:
            self.update({'zone_id':False})
        else:
            self.update({'zone_id':self.lot_id.zone_id.id})
            # self.update({'init_qty':self.stack_id.init_qty})
            # self.update({'product_uom_qty':abs((self.stack_id.avg_deduction * self.stack_id.init_qty / 100)-self.stack_id.init_qty)})
            # self.update({'weighbridge':self.stack_id.init_qty})
            self.update({'product_id':self.lot_id.product_id})
            self.update({'packing_id':self.lot_id.packing_id})
            # self.update({'bag_no':self.stack_id.bag_qty})
    
    
    def action_done(self):
        for line in self:
            if not line.stack_id:
                continue
            onhand_stack = line.stack_id.init_qty
            if line.location_id.usage == 'internal' and line.location_dest_id.usage == 'internal':
                if onhand_stack < line.init_qty :
                    stt = u''' Stact %s tồn kho: %s nhỏ  hơn lượng xuất : %s''' %(line.stack_id.name,onhand_stack,line.init_qty)
                    raise UserError(_(stt))
            
            #THANH: Update the same stock_move with date done of stock_picking
            #Kiet goi su kien stack
        for move in self:
            super(StockMove,self).action_done()
#             if move.stack_id:
#                 move.stack_id.btt_expenses()
                #kiet kiểm tro tồn kho Stack khong xuất ấm
        return True
    
    def create_stack(self):
        pcontract = self.env['s.contract']
        for this in self:
            if this.stack_id:
                raise UserError(_('Warning !!!'))
            if not this.zone_id:
                raise UserError(_('Warning !!!'))
            
            var = {
                    'zone_id':this.zone_id.id,
                    'date':time.strftime('%Y-%m-%d'),
                    'p_contract_id': this.picking_id.pcontract_id and this.picking_id.pcontract_id.id or 0
                  }
            stack_id = False
            if this.picking_id.pcontract_id:
                stack_id = this.picking_id.pcontract_id.wr_line or False
            if not stack_id:
                stack_id = self.env['stock.stack'].create(var)
                if self.context.get('pcontract_id', False):
                    this.picking_id.pcontract_id.write({'wr_line': stack_id.id})
            this.stack_id = stack_id
        return 1
    
    
    
