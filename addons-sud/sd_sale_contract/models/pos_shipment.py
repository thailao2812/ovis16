# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class PostShipMent(models.Model):
    _name = "post.shipment"
    # _inherit = ['mail.thread'] #SON Add
    
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('post.shipment') or 'New'
        result = super(PostShipMent, self).create(vals)
        return result
    
    name = fields.Char(string="Ps No.", required = True, default='/')
    do_id = fields.Many2one('delivery.order', string='DO no.',  index=True, copy=False)
    nvs_nls_id = fields.Many2one('sale.contract', string='NVS - NLS', copy=False)
    truck_plate = fields.Char(string= "Truck No.",size=128)
    post_line = fields.One2many('post.shipment.line', 'post_id', string='Post Shipment Lines')
    delivery_place_id = fields.Many2one('delivery.place', string='Delivery Place')
    notes = fields.Text(string='Notes')
    packing_id = fields.Many2one('ned.packing', string='Packing')
    do_id = fields.Many2one('delivery.order', string='DO no.',  index=True, copy=False)
    shipping_id = fields.Many2one('shipping.instruction', string='SI No.', copy=False)
    state = fields.Selection([('draft', 'New'), ('approved', 'Approved'), ('done', 'Done'), ('cancel', 'Cancelled')],
             string='Status', readonly=True, copy=False, index=True, default='draft')

    cont_no = fields.Char('Cont no.', related='post_line.cont_no', readonly=True, store =True)
    bl_no = fields.Char('B/L no.', related='post_line.bl_no', readonly=True, store =True)
    
    def button_load(self):
        if self.do_id:
            self.env.cr.execute('''DELETE FROM post_shipment_line WHERE post_id = %s''' % (self.id))
    
            val ={
                  'nvs_nls_id':self.do_id.contract_id and self.do_id.contract_id.id or False,
                  'delivery_place_id':self.do_id.delivery_place_id and self.do_id.delivery_place_id.id or False,
                  'truck_plate':self.do_id.trucking_no or False,
                  'packing_id':self.do_id.packing_id and self.do_id.packing_id.id or False,
                  'shipping_id':self.do_id.shipping_id and self.do_id.shipping_id.id or False
                  }
            self.write(val)
        return True
    
    def button_draft(self):
        self.write({'state': 'draft'})
 
    
    def button_approve(self):
        self.write({'state': 'approved'})
                        
class PostShipMentLine(models.Model):
    _name = "post.shipment.line"
    
    cont_no = fields.Char(string ='Cont no.',size =128,required = True)
    loading_date = fields.Date(string='Loading date')
    post_id= fields.Many2one('post.shipment', string='Post no.')
    bags = fields.Float(string ='Bags',digits=(12, 0) )
    shipped_weight = fields.Float(string ='Shipped weight',digits=(12, 0) )
    bl_date = fields.Date(string='B/L date')
    bl_no = fields.Char(string ='B/L no.',size =128,required = False)
    supervisor_id = fields.Char(string= 'Supervisor',size =128)
    nvs_nls_id = fields.Many2one('sale.contract',related='post_id.nvs_nls_id',  string='NVS - NLS',store=True)
    do_id = fields.Many2one('delivery.order',related='post_id.do_id',  string='Do no.',store=True)
    
    # lot_id = fields.Many2one('lot.kcs', string='Lot manager')
    # lot_ned = fields.Char(related='lot_id.lot_ned', string='Lot Ned',store =True)
    
    
    
    
