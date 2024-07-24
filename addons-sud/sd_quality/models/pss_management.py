# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from datetime import datetime
    
class PssManagement(models.Model):
    _name="pss.management"
    
    @api.onchange('shipping_id')
    def onchange_bags_qty(self):
        traffic_obj = self.env['traffic.contract']
        for rc in self:
            if rc.shipping_id:
                contract_name = rc.shipping_id.contract_id and rc.shipping_id.contract_id.name or ''
                traffic_id = traffic_obj.search([('name', '=', contract_name)], limit=1)
                rc.partner_id = rc.shipping_id.partner_id.id if rc.shipping_id.partner_id else False
                rc.product_id = rc.shipping_id.shipping_ids[0].product_id.id if rc.shipping_id.shipping_ids else False
                if traffic_id:
                    traffic_info = traffic_obj.browse(traffic_id.id)
                    rc.ship_by = traffic_info.shipby_id and traffic_info.shipby_id.id or ''
                    rc.shipper_id = traffic_info.shipper_id and traffic_info.shipper_id or ''
    
    
    @api.onchange('stack')
    def onchange_stack(self):
        for i in self:
            if not i.stack:
                i.mc = 0
                i.fm = 0
                
                i.black= 0
                i.broken = 0
                i.brown = 0
                i.moldy = 0
                i.burned = 0
                i.scr20= 0
                i.scr19= 0 
                i.scr18= 0
                i.scr16= 0
                i.scr13= 0
                i.scr12= 0
                i.blscr12= 0
                
            for stack in i.stack:
                i.mc = stack.mc
                i.fm = stack.fm
                i.black= stack.black
                i.broken = stack.broken
                i.brown = stack.brown
                i.moldy =stack.mold
                i.burned = stack.burn
                i.scr20= stack.screen20
                i.scr19= stack.screen19
                i.scr18= stack.screen18
                i.scr16= stack.screen16
                i.scr13= stack.screen13
                i.scr12= stack.greatersc12
                i.blscr12= stack.screen12
                
                    

    ship_by = fields.Many2one('s.ship.by', string='Shipped By')
    shipper_id = fields.Char(string='Shipper', size=256)
    
    @api.onchange('shipping_id')
    def _x_stuff_place(self):
        traffic_obj = self.env['traffic.contract']
        for rc in self:
            if rc.shipping_id:
                contract_name = rc.shipping_id.contract_id and rc.shipping_id.contract_id.name or ''
                traffic_contract = traffic_obj.search([('name', '=', contract_name)], limit=1)
                rc.x_stuff_place = traffic_contract and traffic_contract.x_stuff_place or False
    
    x_stuff_place = fields.Char(string='Stuffing Place', size=256)

    name = fields.Char(string="PSS name")
    shipping_id = fields.Many2one("shipping.instruction", string="SI No.")
    created_date =  fields.Date(string="Date")
    date_sent = fields.Date(string="Date sent")
    pss_status = fields.Selection([('pending', 'Pending'), ('sent', 'Sent'), ('approved', 'Approved'), ('rejected','Rejected')], string="PSS status")
    date_result = fields.Char(string="Date result")
    product_id = fields.Many2one("product.product", string="Product")
    buyer_ref = fields.Char(string="Buyer ref.")
    lot_quantity = fields.Float(string="Quantity")
    cont_quantity = fields.Float(string="Cont. qty.")
    mc = fields.Float(string="MC")
    fm = fields.Float(string="FM")
    black = fields.Float(string="Black")
    broken = fields.Float(string="Broken")
    brown = fields.Float(string="Brown")
    moldy = fields.Float(string="Moldy")
    burned = fields.Float(string="Burned")
    scr20 = fields.Float(string="Screen 20")
    scr19 = fields.Float(string="Screen 19")
    scr18 = fields.Float(string="Screen 18")
    scr16 = fields.Float(string="Screen 16")
    scr13 = fields.Float(string="Screen 13")
    scr12 = fields.Float(string="Screen 12")
    blscr12 = fields.Float(string="Below scr.12")
    stack = fields.Many2many("stock.lot", string="Stack no.")
    ref_no = fields.Char(string="Reference")
    inspector = fields.Char(string="Inspector")
    buyer_comment = fields.Char(string="Buyer's comment")
    our_comment = fields.Char(string="Our comment")
    note = fields.Char(string="Note")
    qc_staff = fields.Char(string="QC staff")
    partner_id = fields.Many2one("res.partner", string="Customer")
    x_bulk_density = fields.Char(string='Bulk Density', size=256)
    x_shipment_date = fields.Date(related='shipping_id.shipment_date', string='Shipment Date', store=True)
    x_ex_warehouse_id = fields.Many2one("x_external.warehouse", string="Ex Warehouse")
    status_nestle = fields.Selection([
        ('sent', 'Sent'),
        ('approved', 'Approved'),
        ('reject_phys', 'Rejected Physical'),
        ('reject_gly', 'Rejected Glyphosate'),
        ('reject_cupping', 'Rejected Cupping')
    ], string='PSS Status Nestle')
    is_nestle = fields.Boolean(string='Is Nestle', default=False)
    file = fields.Binary(string='File')
    file_name = fields.Char(string='File Name')

    def load_si_info(self):
        if self.id:
            self.partner_id = self.shipping_id.partner_id
            self.product_id = self.shipping_id.product_id
        return True

    @api.model
    def create(self, vals):
        new_id = super(PssManagement, self).create(vals)
        new_id.onchange_stack()
        return new_id
    
    
