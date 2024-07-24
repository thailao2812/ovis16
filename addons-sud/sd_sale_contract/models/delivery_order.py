# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from datetime import datetime
from pytz import timezone


DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class DeliveryOrder(models.Model):
    _name = "delivery.order"
    _description = "Delivery Order"
    _inherit = ['mail.thread'] #SON Add
    _order = 'id desc'
    
    
    def printout_deilvery_order(self):
        return 
        # if self.type == 'sale':
        #     return {'type': 'ir.actions.report.xml', 'report_name': 'report_delivery_orders'}
        # elif self.type == 'Transfer':
        #     return {'type': 'ir.actions.report.xml', 'report_name': 'report_delivery_orders'}
        
    
    @api.model
    def _default_warehouse_id(self):
        company = self.env.user.company_id.id 
        warehouse_ids = self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1)
        return warehouse_ids
    
    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True, default='New')
    state = fields.Selection([('draft', 'New'), ('approved', 'Approved'), ('done', 'Done'), ('cancel', 'Cancelled')],
             string='Status', readonly=True, copy=False, index=True, default='draft')
    
    type_contract = fields.Selection(related="contract_id.type",store = True, string="Type Contract")
    
    date = fields.Date(string='Date', readonly=True, index=True, states={'draft': [('readonly', False)]}, copy=False, default=fields.Datetime.now)
    trucking_id = fields.Many2one('res.partner', string='Trucking Co', readonly=True, required=False, states={'draft': [('readonly', False)]})
    #Lay của ned contract
    # transrate = fields.Float(string='Trans Rate (VND)', required=True, readonly=True, index=True, states={'draft': [('readonly', False)]}, copy=False)
    
    @api.model
    def _default_currency_id(self):
        currency_id = self.env.user.company_id.currency_id.id
        return currency_id
    
    currency_id = fields.Many2one("res.currency", string="Currency", readonly=True, required=False, states={'draft': [('readonly', False)]}, default=_default_currency_id)
    
    
    create_date = fields.Date(string='Creation Date', readonly=True, index=True, default=fields.Datetime.now)
    create_uid = fields.Many2one('res.users', 'Responsible', readonly=True , default=lambda self: self._uid)
    date_approve = fields.Date('Approval Date', readonly=True, copy=False)
    user_approve = fields.Many2one('res.users', string='User Approve', readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=False, readonly=True, states={'draft': [('readonly', False)]})
    picking_type_id = fields.Many2one("stock.picking.type", string="Reason", readonly=True, required=False, states={'draft': [('readonly', False)]})
    
    partner_id = fields.Many2one("res.partner", string="Customer", readonly=True, states={'draft': [('readonly', False)]})
    vehicle_manufacture = fields.Char(string="Vehicle Manufacture", readonly=True, states={'draft': [('readonly', False)]})
    trucking_no = fields.Char(string="Trucking No.", readonly=True, states={'draft': [('readonly', False)]})
    driver_name = fields.Char(string="Driver's Name", readonly=True, states={'draft': [('readonly', False)]})
    registration_certificate = fields.Char(string="Registration Certificate", readonly=True, states={'draft': [('readonly', False)]})
    company_ref_guide = fields.Char(string="Company Ref. Guide", readonly=True, states={'draft': [('readonly', False)]})
    transporter_ref_guide = fields.Char(string="Transporter Ref. Guide", readonly=True, states={'draft': [('readonly', False)]})
    
    contract_id = fields.Many2one("sale.contract", string="Contract No.", required=False, readonly=True, states={'draft': [('readonly', False)]}, ondelete='cascade')
    markings = fields.Text(string="Markings", readonly=True, states={'draft': [('readonly', False)]})
    reason = fields.Text(string="Reason", readonly=True, states={'draft': [('readonly', False)]})
    picking_id = fields.Many2one("stock.picking", string="GDN No.")
#     invoice_state = fields.Selection(selection=[("invoiced", "Invoiced"), ("2binvoiced", "To Be Invoiced"), ("none", "Not Applicable")],
#                          related="picking_id.invoice_state", string="Invoice Control", readonly=True, copy=False, store=True, default="2binvoiced")          
    
    delivery_order_ids = fields.One2many('delivery.order.line', 'delivery_id', string="DO Lines", readonly=True, states={'draft': [('readonly', False)]})
    post_shippemnt_ids = fields.One2many('post.shipment', 'do_id', string="Post Shippment", readonly=True, states={'draft': [('readonly', False)]})
    date_out = fields.Date(string='Date out', readonly=False, index=True,copy = False)
    received_date = fields.Date(string='Received date', readonly=False, index=True,copy = False)
    
    #Kiet doan nay lay của add_ned thêm fields
    shipping_id = fields.Many2one(related='contract_id.shipping_id',  string='SI No.',store=True)
    
    # Thai lao 29/11
    is_bonded = fields.Selection([
        ('none', 'None'),
        ('transfer', 'Transfer')
    ], string='Is Transfer Bonded', default='none')
    
    #Thai Lao 31/03
    date_invoice = fields.Date(related='contract_id.date_invoice', store=True, string='Date Invoice')
    
    packing_id = fields.Many2one(related='shipping_id.packing_id', string='Packing', store=True)
    warehouse_id = fields.Many2one(related=False, string='Warehouse', compute=False)

    certificate_id = fields.Many2one('ned.certificate', string='Certificate',
                                     related='shipping_id.certificate_id', store=True)
    
    #DIm lại lấy của ned contract
    # type= fields.Selection([('Sale', 'Sale'), ('Transfer', 'Transfer')],
    #          string='Type')
    
    @api.depends('delivery_order_ids','delivery_order_ids.product_qty')
    def _total_qty(self):
        for order in self:
            total_qty = 0
            for line in order.delivery_order_ids:
                total_qty += line.product_qty
            order.total_qty = total_qty
    
    
    
    total_qty = fields.Float(compute='_total_qty', digits=(16, 0) , string='Qty (kg)',store=True)
    product_id = fields.Many2one(related='delivery_order_ids.product_id',  string='Product',store=True)
    
    #Lay của ned contract
    # @api.model
    # def create(self, vals):
    #     if vals.get('name', False):
    #         if vals.get('type',False) == 'Sale':
    #             vals['name'] = self.env['ir.sequence'].next_by_code('delivery.order')
    #         else:
    #             vals['name'] = self.env['ir.sequence'].next_by_code('delivery.order.transfer')
    #     else:
    #         name = vals.get('name', False)
    #         do_ids = self.search([('name', '=', name)])
    #         if len(do_ids) >= 1:
    #             raise UserError(_("Delivery Orders (%s) was exist.") % (name))
    #     result = super(DeliveryOrder, self).create(vals)
    #     return result
    
    def unlink(self):
        if self.state not in ('draft', 'approved', 'cancel'):
            raise UserError(_('You cannot delete a Delivery Order approved.'))
        
        picking_pool = self.env['stock.picking']
        picking_id = picking_pool.search([('delivery_id', '=', self.id)])
        if picking_id:
#             if picking_id.invoice_state == 'invoiced':
#                 raise UserError(_('You cannot delete a Delivery Order has an invoice.'))
        
            self.env.cr.execute('''DELETE FROM stock_pack_operation WHERE picking_id = %(picking_id)s;
                DELETE FROM stock_move WHERE picking_id = %(picking_id)s;
                DELETE FROM stock_picking WHERE id = %(picking_id)s; ''' % ({'picking_id': picking_id.id}))
        return super(DeliveryOrder, self).unlink()
    
    
    @api.onchange('warehouse_id')
    def onchange_warehouse_id(self):
        if not self.warehouse_id:
            return
        domain = {'picking_type_id': [('id', '=', self.warehouse_id.out_type_id.id)]}
        values = {'picking_type_id': self.warehouse_id.out_type_id.id or False}
        self.update(values)
        return {'domain': domain}
    
    
    def button_load_do(self):
        sql ='''
            SELECT '%s'::date as date
        '''%(self.date)
        self.env.cr.execute(sql)
        for date in self.env.cr.dictfetchall():
            received_date = date['date'] or 0.0
        self.write({
                    'received_date':received_date})
        
        if self.contract_id: 
            
            self.env.cr.execute('''DELETE FROM delivery_order_line WHERE delivery_id = %s''' % (self.id))
            val ={
                  'partner_id':self.contract_id.partner_id and self.contract_id.partner_id.id or False,
                  'warehouse_id':self.contract_id.warehouse_id and self.contract_id.warehouse_id.id,
                  'reason': u'Vận chuyển nội bộ',
                  'delivery_place_id':self.contract_id.shipping_id.delivery_place_id and self.contract_id.shipping_id.delivery_place_id.id or False,
                  'markings':self.contract_id.shipping_id.marking or False,
                  'packing_place': self.contract_id.shipping_id.packing_place or False
                  }
            self.write(val)
            product_qty = new_qty = 0.0
            for contract in self.contract_id.contract_line:
                for do in self.contract_id.delivery_ids:
                    if do.state != 'cancel':
                        for do_line in do.delivery_order_ids:
                            if do_line.product_id == contract.product_id:
                                product_qty += do_line.product_qty
                new_qty = contract.product_qty - product_qty 
                var = {'delivery_id': self.id, 'name': contract.name, 'product_id': contract.product_id.id,
                       'certificate_id':self.contract_id.shipping_id.certificate_id.id,
                       'packing_id': self.contract_id.shipping_id.packing_id.id,
                       
                       'product_qty': new_qty, 'product_uom': contract.product_uom.id, 'state': 'draft'}
                self.env['delivery.order.line'].create(var)
        return True
    
    
    def button_draft(self):
        if self.state == 'approved':
            picking_id = self.picking_id
#             if picking_id and picking_id.invoice_state == 'invoiced':
#                 raise UserError(_('Unable to cancel Delivery Order %s.') % (self.name))
            if picking_id.state not in ('confirmed','assigned','done','approved'):
                picking_id.unlink()
            else:
                raise UserError(_('Unable to cancel Delivery Order %s.') % (self.name))
        self.write({'state': 'draft'})
 
    
    def button_approve(self):
        self.write({'state': 'approved', 'user_approve': self.env.uid,
                    'date_out':datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                     'date_approve': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
                        
    def button_done(self):
        picking_pool = self.env['stock.picking']
        picking_id = picking_pool.search([('delivery_id', '=', self.id)])
        if not picking_id:
            raise UserError(_('You cannot done a Delivery Order without a GDN.'))
        self.write({'state': 'done'})


######################################### NED Contract ############################################################################
    
    type= fields.Selection([
        ('Sale', 'Sale'), 
        ('Transfer', 'Transfer'),
        ('bonded', 'Bonded')], string='Type')

    transrate = fields.Float(
        string='Trans Rate (VND)', 
        required=False, 
        readonly=True, index=True, states={'draft': [('readonly', False)]})

    @api.model
    def create(self, vals):
        # if vals.get('name', False):
        if vals.get('type',False) == 'Sale':
            vals['name'] = self.env['ir.sequence'].next_by_code('delivery.order')
        else:
            vals['name'] = self.env['ir.sequence'].next_by_code('delivery.order.transfer')
        # else:
        #     name = vals.get('name', False)
        #     do_ids = self.search([('name', '=', name)])
        #     if len(do_ids) >= 1:
        #         raise UserError(_("Delivery Orders (%s) was exist.") % (name))
        
        if vals.get('type', False) == 'bonded':
            name = vals.get('name', False)
            do_ids = self.search([('name', '=', name)])
            if len(do_ids) >= 1:
                raise UserError(_("Ex-stored (%s) was exist.") % (name))
        return super(DeliveryOrder, self).create(vals)

    
   
    
    delivery_place_id = fields.Many2one(related='contract_id.shipping_id.delivery_place_id', string='Delivery Place',
        required=False)    
    shipping_id = fields.Many2one(related='contract_id.shipping_id',  string='SI No.',store=True)
    move_id = fields.Many2one('stock.move',string='Move')
    
    packing_qty = fields.Integer(string='Real Ex-stored (bag)')
    real_qty = fields.Float(string='Real Ex-stored (kg)')

    #Duy them dia diem dong hang
    packing_place = fields.Selection([('factory','Factory-BMT'),
                                      ('sg','HCM'), # shortened from HCM
                                      ('bd','Binh Duong'),
                                      ('mn','Kho Molenberg Natie'),
                                      ('vn','Kho Vinacafe'),
                                      ('kn','Kho Katoen LT'),
                                      ('ka', 'Kho Katoen AP'),
                                      ('pa', 'Kho Pacorini')], string='Stuffing place')
    
    #err chưa ổn vì còn bên ned stock chưa đêm wa 
    # dim lai lay theo stock warehouse
    # @api.depends('packing_place','post_shippemnt_ids.post_line','post_shippemnt_ids','post_shippemnt_ids.post_line.bags','post_shippemnt_ids.post_line.shipped_weight')
    # def _factory_qty(self):
    #     for order in self:
    #         if order.type == 'Transfer':
    #             weight_out = weight_in = bags_out = bags_in = 0
    #             pick_id = self.env['stock.picking'].sudo().search([('delivery_order_id','=',order.id)])
    #             for pick in pick_id:
    #                 if pick.state == 'done':
    #                     # print pick.state, pick.picking_type_code
    #                     # Duyệt stock_picking rows lấy các dòng transfer local
    #                     if pick.picking_type_code == 'transfer_out' or pick.picking_type_code == 'outgoing': #152:
    #                         for line in pick.move_lines:
    #                             if line.weighbridge == 0:
    #                                 weight_out += line.init_qty
    #                             else:
    #                                 weight_out += line.weighbridge
    #                             bags_out += line.bag_no or 0.0
    #                     if pick.picking_type_code == 'transfer_in' or pick.picking_type_code == 'incoming': #104:                    
    #                         for line in pick.move_lines:
    #                             if line.weighbridge == 0:
    #                                 weight_in += line.init_qty
    #                             else:
    #                                 weight_in += line.weighbridge
    #                             bags_in += line.bag_no or 0.0
    #             #         print weight_out, weight_in
    #
    #             #     print pick.id
    #             # print weight_out, weight_in, 'STOP', order.id
    #             order.weightfactory = weight_out
    #             order.bagsfactory = bags_out
    #             order.shipped_weight = weight_in
    #             order.bags = bags_in
    #             order.storing_loss = order.total_qty -  order.weightfactory
    #             order.transportation_loss = order.weightfactory -  order.shipped_weight
    #
    #                     # # Duyệt stock_picking rows lấy các dòng transfer MBN
    #                     # if pick.picking_type_id['code'] == 183:
    #                     #     for line in pick.move_lines:
    #                     #         weight_out += line.weighbridge or 0.0
    #                     #         bags_out += line.bag_no or 0.0
    #                     # if pick.picking_type_id['code'] == 174:                    
    #                     #     for line in pick.move_lines:
    #                     #         weight_in += line.init_qty or 0.0
    #                     #         bags_in += line.bag_no or 0.0
    #
    #         if order.type == 'Sale':
    #             weight = bagsfactory  = 0
    #             for pick in order.picking_id:
    #                 if pick.state == 'done':
    #                     for line in pick.move_lines:
    #                         bagsfactory += line.bag_no or 0.0
    #                         weight += line.init_qty or 0.0 
    #
    #             for post in order.post_shippemnt_ids:
    #                 shipped_weight = bags  = 0
    #                 for line in post.post_line:
    #                     bags += line.bags
    #                     shipped_weight += line.shipped_weight
    #
    #
    #
    #             if order.packing_place == 'factory':
    #                 order.bagsfactory = bagsfactory
    #                 order.weightfactory = weight
    #                 order.bags = bagsfactory
    #                 order.shipped_weight = weight
    #                 order.storing_loss = order.total_qty -  weight 
    #                 order.transportation_loss = 0
    #             else:
    #                 order.bags = bags
    #                 order.shipped_weight = shipped_weight
    #
    #                 order.bagsfactory = bagsfactory
    #                 order.weightfactory = weight
    #                 order.storing_loss = order.total_qty - weight 
    #                 order.transportation_loss = weight - shipped_weight
                
            
    bagsfactory = fields.Float(compute='_factory_qty', digits=(12, 0) , string='Bags Factory',store =True)
    weightfactory = fields.Float(compute='_factory_qty', digits=(12, 0) , string='Weight Factory (kg)',store =True)
    
    storing_loss  = fields.Float(compute='_factory_qty', digits=(12, 0) , string='Storing Loss (kg)',store =True)
    transportation_loss  = fields.Float(compute='_factory_qty', digits=(12, 0) , string='Trans. Loss (kg)',store =True)
    bags = fields.Float(compute='_factory_qty', digits=(12, 0) , string='Bags HCM',store =True)
    shipped_weight = fields.Float(compute='_factory_qty', digits=(12, 0) , string='Weight HCM (kg)',store =True)
    
    
    
##########################################END NED Contract###########################################################################


########################################## NED STOCK###########################################################################
    
    def compute_factory_qty(self):
        for i in self:
            i._factory_qty()
    
    @api.depends('picking_id', 'picking_id.state', 'packing_place', 'post_shippemnt_ids.post_line',
                 'post_shippemnt_ids', 'post_shippemnt_ids.post_line.bags',
                 'post_shippemnt_ids.post_line.shipped_weight', 'contract_id', 'contract_id.type')
    def _factory_qty(self):
        for order in self:
            if order.type == 'Transfer':
                weight_out = weight_in = bags_out = bags_in = 0
                pick_id = self.env['stock.picking'].sudo().search([('delivery_id', '=', order.id)])
                for pick in pick_id:
                    if pick.state == 'done':
                        # print pick.state, pick.picking_type_code
                        # Duyệt stock_picking rows lấy các dòng transfer local
                        if pick.picking_type_id.code == 'transfer_out' or pick.picking_type_code == 'outgoing':  # 152:
                            for line in pick.move_line_ids_without_package:
                                if line.weighbridge == 0:
                                    weight_out += line.init_qty
                                else:
                                    weight_out += line.weighbridge
                                bags_out += line.bag_no or 0.0
                        if pick.picking_type_id.code == 'transfer_in' or pick.picking_type_code == 'incoming':  # 104:
                            for line in pick.move_line_ids_without_package:
                                if line.weighbridge == 0:
                                    weight_in += line.init_qty
                                else:
                                    weight_in += line.weighbridge
                                bags_in += line.bag_no or 0.0
                #         print weight_out, weight_in
                #     print pick.id
                # print weight_out, weight_in, 'STOP', order.id
                order.weightfactory = weight_out
                order.bagsfactory = bags_out
                order.shipped_weight = weight_in
                order.bags = bags_in
                order.storing_loss = order.total_qty - order.weightfactory
                order.transportation_loss = order.weightfactory - order.shipped_weight

                # # Duyệt stock_picking rows lấy các dòng transfer MBN
                # if pick.picking_type_id['code'] == 183:
                #     for line in pick.move_lines:
                #         weight_out += line.weighbridge or 0.0
                #         bags_out += line.bag_no or 0.0
                # if pick.picking_type_id['code'] == 174:
                #     for line in pick.move_lines:
                #         weight_in += line.init_qty or 0.0
                #         bags_in += line.bag_no or 0.0

            if order.type == 'Sale':
                weight = bagsfactory = 0
                for pick in order.picking_id:
                    if pick.state == 'done':
                        for line in pick.move_line_ids_without_package:
                            bagsfactory += line.bag_no or 0.0
                            weight += line.init_qty or 0.0

                shipped_weight = bags = 0
                for post in order.post_shippemnt_ids:
                    for line in post.post_line:
                        bags += line.bags
                        shipped_weight += line.shipped_weight

                if order.packing_place == 'factory':
                    order.bagsfactory = bagsfactory
                    order.weightfactory = weight
                    order.bags = bagsfactory
                    order.shipped_weight = weight
                    order.storing_loss = order.total_qty - weight
                    order.transportation_loss = 0
                else:
                    order.bags = bags
                    order.shipped_weight = shipped_weight

                    order.bagsfactory = bagsfactory
                    order.weightfactory = weight
                    order.storing_loss = order.total_qty - weight
                    order.transportation_loss = weight - shipped_weight

                if order.contract_id and order.contract_id.type == 'export':
                    if order.picking_id and ('KTN' in order.picking_id.name or 'CWT' in order.picking_id.name):
                        order.shipped_weight = weight
                        order.transportation_loss = 0
                    
                    
    
    storing_loss  = fields.Float(compute='_factory_qty', digits=(12, 0) , string='Storing Loss (kg)',store =True)
    transportation_loss  = fields.Float(compute='_factory_qty', digits=(12, 0) , string='Trans. Loss (kg)',store =True)
    bags = fields.Float(compute='_factory_qty', digits=(12, 0) , string='Bags In',store =True)
    shipped_weight = fields.Float(compute='_factory_qty', digits=(12, 0) , string='Weight IN (kg)',store =True)
    from_warehouse_id= fields.Many2one('stock.warehouse',string="From Warehouse", default=_default_warehouse_id , required =True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=False, readonly=True, states={'draft': [('readonly', False)]})
    
    def create_picking(self):
        for this in self:
            form_picking_type = this.from_warehouse_id.out_type_id
            if this.type =='Transfer':
                form_picking_type = this.from_warehouse_id.transfer_out_id
            var = {'name': '/',
                    'delivery_order_id': this.id,
                    'picking_type_id': form_picking_type.id or False, 
                    'scheduled_date': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT), 
                    'origin':this.name,
                    'partner_id': this.partner_id.id or False,
                    'picking_type_code': form_picking_type.code or False,
                    'location_id': form_picking_type.default_location_src_id.id or False, 
                    'vehicle_no':this.trucking_no or '',
                    'location_dest_id': form_picking_type.default_location_dest_id.id or False,
                    'scheduled_date': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)}
            picking_id = self.env['stock.picking'].create(var)  
            for line in this.delivery_order_ids:
                product_id = line.product_id
                self.env['stock.move.line'].create({'picking_id': picking_id.id or False, 
                        'name': product_id.name or '', 
                        'product_id': product_id.id or False,
                        'product_uom': product_id.uom_id.id or False, 
                        'product_uom_qty':  0.0,
                        'init_qty': 0.0,
                        'price_unit': 0.0,
                        'picking_type_id': form_picking_type.id or False, 
                        'location_id': form_picking_type.default_location_src_id.id or False, 
                        'date_expected': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                        'location_dest_id': form_picking_type.default_location_dest_id.id or False, 
                        'type': form_picking_type.code or False,
                        'date': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT), 
                        'partner_id': this.partner_id.id or False,
                        'company_id': 1,
                        'state':'draft', 
                        'scrapped': False, 
                        'warehouse_id': this.from_warehouse_id.id or False})
            
        return picking_id
    
    def fix_factory_qty(self):
        for order in self:
            if order.type == 'Transfer':
                weight_out = weight_in = bags_out = bags_in = 0
                pick_id = self.env['stock.picking'].sudo().search([('delivery_order_id','=',order.id)])
                for pick in pick_id:
                    if pick.state == 'done':
                        if pick.picking_type_code == 'transfer_out' or pick.picking_type_code == 'outgoing': #152:
                            for line in pick.move_lines:
                                if line.weighbridge == 0:
                                    weight_out += line.init_qty
                                else:
                                    weight_out += line.weighbridge
                                bags_out += line.bag_no or 0.0
                        if pick.picking_type_code == 'transfer_in' or pick.picking_type_code == 'incoming': #104:                    
                            for line in pick.move_lines:
                                if line.weighbridge == 0:
                                    weight_in += line.init_qty
                                else:
                                    weight_in += line.weighbridge
                                bags_in += line.bag_no or 0.0
                order.weightfactory = weight_out
                order.bagsfactory = bags_out
                order.shipped_weight = weight_in
                order.bags = bags_in
                order.storing_loss = order.total_qty -  order.weightfactory
                order.transportation_loss = order.weightfactory -  order.shipped_weight

            if order.type == 'Sale':
                weight = bagsfactory  = 0
                for pick in order.picking_id:
                    if pick.state == 'done':
                        for line in pick.move_lines:
                            bagsfactory += line.bag_no or 0.0
                            weight += line.init_qty or 0.0 
                
                shipped_weight = bags  = 0
                for post in order.post_shippemnt_ids:
                    for line in post.post_line:
                        bags += line.bags
                        shipped_weight += line.shipped_weight
                                       
                if order.packing_place == 'factory':
                    order.bagsfactory = bagsfactory
                    order.weightfactory = weight
                    order.bags = bagsfactory
                    order.shipped_weight = weight
                    order.storing_loss = order.total_qty -  weight 
                    order.transportation_loss = 0
                else:
                    order.bags = bags
                    order.shipped_weight = shipped_weight
                    
                    order.bagsfactory = bagsfactory
                    order.weightfactory = weight
                    order.storing_loss = order.total_qty -  weight 
                    order.transportation_loss = weight -  shipped_weight

##########################################END NED STOCK ###########################################################################

    
    ######################## Kiet các fields mới 24/04/2023
    origin = fields.Char(string='Origin')
    date_done = fields.Date(string='Date Done')
    date_transfer= fields.Date(string='Date Transfer')
    message_last_post = fields.Datetime(string='Message Last Post')
    location_id = fields.Many2one('stock.location', string="Location")
    city = fields.Char(string='City')
    sale_contract_id = fields.Many2one('sale.contract', string="Sales Contract")
    country_id = fields.Many2one('res.country', string="Sales Contract")
    company_id = fields.Many2one('res.company', string="Company")
    note = fields.Text(string='Notes')
    min_date = fields.Date(string="Min date")
    location_dest_id = fields.Many2one('stock.location', string="Location Dest")
    state_id = fields.Many2one("res.country.state", string= 'State')
    district = fields.Char(string="District")
    priority = fields.Char(string="Priority")
    partner_shipping_id = fields.Many2one("res.partner", string= 'Partner')
    drive_license_no = fields.Char(string="Drive License No")
    shipment_from= fields.Many2one("delivery.place", string= 'Shipment From')
    transportation_cost = fields.Float(string="Transportation Cost")
    recipient = fields.Char(string='Recipient')
    vehicle_no = fields.Char(string='Vehicle No')
    invoice_state = fields.Char(string='Invoice State')
    delivery_place_id = fields.Many2one("delivery.place", string= 'Delivery Place')
    gdn_no = fields.Char(string='GDN No')
    state_kcs = fields.Char(string='State Kcs')
    
    
class DeliveryOrderLine(models.Model):
    _name = "delivery.order.line"
        
    name = fields.Text(string='Description', required=True)
    delivery_id = fields.Many2one('delivery.order', string='Delivery Order', ondelete='cascade', index=True, copy=False)
    sequence = fields.Integer(string='Sequence', default=10)
    state = fields.Selection(selection=[('draft', 'New'), ('approved', 'Approved'), ('cancel', 'Cancelled')],
          related='delivery_id.state', string='Status', readonly=True, copy=False, store=True, default='draft')
    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)], change_default=True, required=True)
    product_qty = fields.Float(string='Qty', required=True, default=1.0)
    product_uom = fields.Many2one('uom.uom', string='Uom', required=True)  
    price_unit = fields.Float('Unit Price', default=0.0)
    tax_id = fields.Many2many('account.tax', string='Taxes')  
    
######################################### NED Contract ############################################################################
    
    packing_id = fields.Many2one('ned.packing', string='Packing')
    certificate_id = fields.Many2one('ned.certificate', string='Certificate')
##########################################END NED Contract###########################################################################

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.default_code + ' ' + self.product_id.name
            self.product_uom = self.product_id.uom_id.id