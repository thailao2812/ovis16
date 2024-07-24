# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from datetime import datetime
import time
from datetime import timedelta
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"   
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import timedelta, datetime, date
    
class LotStackAllocation(models.Model):
    _name ="lot.stack.allocation"
    _order = "id desc"
    
    lot_id = fields.Many2one('lot.kcs',string="Lot no.")
    rel_lot_kcs_approved = fields.Selection(string="rel_lot_kcs_approved",related='lot_id.state',)
    quantity = fields.Float(string="Quantity")
    delivery_id = fields.Many2one('delivery.order',string="Do no.")
    state = fields.Selection([('draft', 'Draft'), ('approve', 'Approve')], string="State", required=True, default="draft")
    grp_id = fields.Many2one('stock.picking',string="GRP", domain="[('state', '=', 'done'),('picking_type_id.code', 'in', ('production_in','incoming'))]")
    stack_id = fields.Many2one('stock.lot', string="Stack", readonly=False)
    contract_id = fields.Many2one(related='lot_id.contract_id',  string='S Contract',store = True)
    zone_id = fields.Many2one('stock.zone',related='stack_id.zone_id', string="Zone", readonly=True,store=True)
    mc_on_despatch = fields.Float(string="Mc On Despatch")
    cuptaste = fields.Char(string="Cuptaste",)
    defects = fields.Float(string="Defects-ISO",  digits=(12, 2), ) 
    defects_tcvn = fields.Float(string="Defects-TCVN",  digits=(12, 2), ) 
    gdn_id = fields.Many2one('stock.picking',string="GDN",readonly=True) 
    product_id = fields.Many2one(related='lot_id.product_id',string="Product",readonly=True,store=True) 
    # nvs_id = fields.Many2one(related='lot_id.nvs_id', string="NVS - NLS",readonly=True,store=True)
    nvs_id = fields.Many2one(related='delivery_id.contract_id', string="NVS - NLS",readonly=True,store=True)
    warehouse_id = fields.Many2one('stock.warehouse', related='stack_id.warehouse_id', store=True)

    no_of_bag = fields.Float(string="No of Bags")
    packing_id = fields.Many2one('ned.packing', related='stack_id.packing_id', store=True)
    shipping_id = fields.Many2one('shipping.instruction', related='delivery_id.shipping_id', store=True)

    @api.onchange("delivery_id", 'lot_id')
    def onchange_delivery_id(self):
        for this in self:
            if this.lot_id:
                this.lot_id.nvs_id = this.delivery_id.contract_id.id


    def btt_confirm(self):
        #self.update_gdn()
        if self.state == 'approve':
            a = "Cannot approve when it was approved"
            raise UserError(_(a))

        # shipping = self.shipping_id
        # stack = self.stack_id
        # shipping_check = self.search([
        #     ('stack_id', '=', stack.id),
        #     ('shipping_id', '!=', shipping.id)
        # ], limit=1)
        # if shipping_check:
        #     raise UserError(_("You cannot choose stack %s for 2 SI: %s and %s") % (stack.name, shipping.name,
        #                                                                            shipping_check.shipping_id.name))

        for this in self:
            warehouse = False
            if not this.stack_id:
                raise UserError(_("Please input Stack before confirm this Lot Allocation!!!"))
            no_of_bag = this.stack_id.bag_qty
            if no_of_bag > 0:
                if this.no_of_bag > no_of_bag:
                    raise UserError(_("Stack: %s have only %s\n"
                                      "But you are input %s > %s of Stack, please input no of bag again")
                                    % (this.stack_id.name, no_of_bag, this.no_of_bag, no_of_bag))
                if this.no_of_bag < 0:
                    raise UserError(_("Cannot input no of bag < 0!!!"))
            if this.delivery_id:
                packing_id = False
                for q in this.stack_id.move_line_ids:
                    if q.location_id.usage == 'production' and q.location_dest_id.usage == 'internal':
                        if q.packing_id:
                            packing_id = q.packing_id.id

                if this.delivery_id.type == 'Sale':

                    if this.quantity == 0:
                        raise UserError(_('Quantity > 0'))
                    picking_type_id = 0
                    if this.delivery_id.from_warehouse_id:
                        warehouse = this.delivery_id.from_warehouse_id
                    if not warehouse:
                        warehouse = this.delivery_id.warehouse_id
                        if not warehouse:
                            company = self.env.user.company_id.id
                            warehouse = self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1)

                    if this.nvs_id.type != 'local':
                        picking_type_id = warehouse.out_type_id
                    else:
                        picking_type_id = warehouse.out_type_local_id

                    if not picking_type_id:
                        raise UserError(_('Need to define Picking Type for this transaction'))

                    if this.delivery_id and not this.delivery_id.picking_id:
                        var = {'name': '/',
                               'picking_type_id': picking_type_id.id or False,
                               'scheduled_date': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                               'origin': this.delivery_id.name,
                               'partner_id': this.delivery_id.partner_id.id or False,
                               'picking_type_code': picking_type_id.code or False,
                               'location_id': picking_type_id.default_location_src_id.id or False,
                               'vehicle_no': this.delivery_id.trucking_no or '',
                               'location_dest_id': picking_type_id.default_location_dest_id.id or False,
                               'delivery_id': this.delivery_id.id,
                               'warehouse_id': warehouse.id
                               # 'min_date': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                               }
                        picking_id = self.env['stock.picking'].create(var)
                        this.delivery_id.picking_id = picking_id.id
                    else:
                        picking_id = this.delivery_id.picking_id

                    if not this.gdn_id:
                        this.gdn_id = picking_id.id

                    self.env['stock.move.line'].create({'picking_id': picking_id.id or False,
                                                        # 'name': this.product_id.name or '',
                                                        'product_id': this.product_id.id or False,
                                                        'product_uom_id': this.product_id.uom_id.id or False,
                                                        'qty_done': this.quantity or 0.0,
                                                        'init_qty': this.quantity or 0.0,
                                                        'bag_no': this.no_of_bag or 0,
                                                        'price_unit': 0.0,
                                                        'picking_type_id': picking_type_id.id or False,
                                                        'location_id': picking_type_id.default_location_src_id.id or False,
                                                        'date': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                                                        'location_dest_id': picking_type_id.default_location_dest_id.id or False,
                                                        # 'type': picking_type_id.code or False,
                                                        # 'date': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                                                        'partner_id': this.lot_id.contract_id.partner_id.id or False,
                                                        'company_id': 1,
                                                        'state': 'draft',
                                                        # 'scrapped': False,
                                                        # 'grp_id':this.grp_id.id,
                                                        'zone_id': this.zone_id.id,
                                                        'lot_id': this.stack_id.id,
                                                        'packing_id': this.packing_id.id,
                                                        'warehouse_id': warehouse.id or False})
                    this.state = 'approve'
                else:
                    if self.delivery_id.type == 'Transfer':
                        warehouse = this.delivery_id.from_warehouse_id
                        move = self.env['stock.move.line']
                        if self.delivery_id.warehouse_id.transfer_out_id:
                            picking_type = self.delivery_id.from_warehouse_id.transfer_out_id
                            if this.delivery_id and not this.delivery_id.picking_id:
                                picking_type = self.delivery_id.from_warehouse_id.transfer_out_id
                                names = self.delivery_id.name
                                val = {
                                    'name': '/',
                                    'picking_type_id': picking_type.id,
                                    'delivery_order_id': self.delivery_id.id,
                                    'location_id': picking_type.default_location_src_id.id,
                                    'location_dest_id': picking_type.default_location_dest_id.id,
                                    'origin': names,
                                    'transfer': False,
                                    'state': 'draft',
                                    'picking_type_code': picking_type.code or False,
                                }
                                picking_id = self.env['stock.picking'].create(val)
                                this.delivery_id.picking_id = picking_id.id
                            else:
                                picking_id = this.delivery_id.picking_id

                            if not this.gdn_id:
                                this.gdn_id = picking_id.id

                            product_id = this.product_id and this.product_id or this.delivery_id.product_id

                            move_vals = {
                                'name': product_id.name or '',
                                'product_id': product_id.id or False,
                                'product_uom': product_id.uom_id.id or False,
                                'product_uom_qty': this.quantity or 0.0,
                                'init_qty': this.quantity or 0.0,
                                'price_unit': 0.0,
                                'picking_id': picking_id.id,
                                'init_qty': this.quantity or 0.0,
                                'product_uom_qty': this.quantity or 0.0,
                                'price_unit': 0.0,
                                'picking_type_id': picking_type.id,
                                'location_id': picking_type.default_location_src_id.id or False,
                                'location_dest_id': picking_type.default_location_dest_id.id or False,
                                'date_expected': time.strftime('%Y-%m-%d %H:%M:%S') or False,
                                'company_id': 1,
                                'state': 'draft', 'scrapped': False,
                                'warehouse_id': warehouse.id or False,
                                'zone_id': this.zone_id.id,
                                'stack_id': this.stack_id.id,
                                'packing_id': packing_id
                            }

                            move.create(move_vals)
                            self.picking_id = picking_id.id
                        this.state = 'approve'
            stk_nqty = this.stack_id.net_qty
            stk_iqty = this.stack_id.init_qty
            this.stack_id.write({
                'net_qty': stk_nqty - this.quantity,
                'init_qty': stk_iqty - this.quantity
            })
            
    def btt_settodraft(self):
        for this in self:
            if this.grp_id:
                move_id = self.env['stock.move.line'].search([('product_id', '=', this.product_id.id),
                                                         ('qty_done', '=', this.quantity),
                                                         ('stack_id', '=', this.stack_id.id),
                                                         ('picking_id', '=', this.grp_id.id)])
                if move_id.picking_id.state == 'done':
                    a = move_id.picking_id.name + u' was Done'
                    raise UserError(_(a))
                if move_id:
                    move_id.unlink()
                this.state = 'draft'
            if this.gdn_id:
                move_id = self.env['stock.move.line'].search([('product_id', '=', this.product_id.id),
                                                         #('qty_done', '=', this.quantity),
                                                         ('lot_id', '=', this.stack_id.id),
                                                         ('picking_id', '=', this.gdn_id.id)])
                if move_id.picking_id.state == 'done':
                    a = move_id.picking_id.name + u' was Done'
                    raise UserError(_(a))
                if move_id:
                    move_id.unlink()
                this.state = 'draft'
            if not this.gdn_id and not this.grp_id:
                this.state = 'draft'
        