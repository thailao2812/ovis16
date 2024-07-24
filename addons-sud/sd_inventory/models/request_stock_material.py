# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
import re
# from pip._vendor.pygments.lexer import _inherit
DATE_FORMAT = "%Y-%m-%d"
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class RequestStockMaterial(models.Model):
    _name = 'request.stock.material'
    
    product_id = fields.Many2one('product.product', related='request_line_ids.product_id', string="Code", store=True)
    description = fields.Char(string='Product', related='product_id.name')

    picking_type_id = fields.Many2one('stock.picking.type', string="Picking Type")
    
    location_id = fields.Many2one('stock.location', 'Source Location')
    location_dest_id = fields.Many2one('stock.location', 'Destination Location')
    picking_id = fields.Many2one('stock.picking', string= 'Picking')
    
    
    def _default_warehouse(self):
        warehouse_ids = self.env['stock.warehouse'].with_context(user_workers=True).search(
            [('company_id', '=', self.env.user.company_id.id)])
        # default with user only working 1 company account analytic
        if warehouse_ids:
            return warehouse_ids[0]
    
    @api.model
    def _domain_warehouse(self):
        return "[('id', 'in', %s)]" % self.env.user._warehouses_domain()
        
    warehouse_id = fields.Many2one('stock.warehouse',string="Warehouse", default=_default_warehouse, domain=lambda self: self._domain_warehouse())
    
    
    @api.onchange('warehouse_id')
    def onchange_warehouse_id(self):
        if self.warehouse_id:
            picking_type_id = self.env['stock.picking.type'].search([
                ('warehouse_id', '=', self.warehouse_id.id),
                ('code', '=', 'material_out')
            ], limit=1)
            self.picking_type_id = picking_type_id.id
            if picking_type_id:
                self.location_id = self.picking_type_id.default_location_src_id.id
                self.location_dest_id = self.picking_type_id.default_location_dest_id.id
                

    name = fields.Char(string='Name')

    type = fields.Selection([('purchase','Purchase'),('manufacturing','Manufacturing')],string="Type", default='manufacturing')

    request_date = fields.Date(string="Request Date", default=datetime.now().date())
    user_id = fields.Many2one('res.users', string="User Request", default=lambda self: self.env.user, readonly=True)

    notes = fields.Text(string='Notes')

    state = fields.Selection([('draft','Draft'),
                                ('approved','Approved'),
                                ('done','Done'),
                                ('cancel','Cancel')], string="State", default='draft')
    
    request_line_ids = fields.One2many('request.stock.material.line','request_id', string="Prodcut")
    
    @api.depends('request_line_ids','request_line_ids.product_qty')
    def _compute_qty(self):
        for req in self:
            totalqty=0.0
            for line in req.request_line_ids:
                totalqty += line.product_qty or 0.0
            req.total_qty = totalqty
    
    total_qty = fields.Float(compute='_compute_qty', store= True, string='Total Qty', digits=(12, 0))

    def button_approve(self):
        if any(x.product_qty == 0 for x in self.request_line_ids):
            raise UserError('Request Quantity must be greather than 0.0.')
        self.state = 'approved'
    
    
    def write(self, vals):
        if vals.get('picking_type_id') and vals.get('warehouse_id'):
            picking_type_id = self.env['stock.picking.type'].search([
                ('warehouse_id', '=', vals.get('warehouse_id')),
                ('code', '=', 'material_out')
            ], limit=1).id
            if vals.get('picking_type_id') != picking_type_id:
                raise UserError(_("You can not change Picking Type"))
        if vals.get('picking_type_id') and not vals.get('warehouse_id'):
            picking_type_id = self.env['stock.picking.type'].search([
                ('warehouse_id', '=', self.warehouse_id.id),
                ('code', '=', 'material_out')
            ], limit=1).id
            if vals.get('picking_type_id') != picking_type_id:
                raise UserError(_("You can not change Picking Type"))
        return super(RequestStockMaterial, self).write(vals)
    
    @api.model
    def create(self,vals):
        if vals.get('picking_type_id') and vals.get('warehouse_id'):
            picking_type_id = self.env['stock.picking.type'].search([
                ('warehouse_id', '=', vals.get('warehouse_id')),
                ('code', '=', 'material_out')
            ], limit=1).id
            if vals.get('picking_type_id') != picking_type_id:
                raise UserError(_('You cannot change Picking Type'))
        
        
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('request.stock.material') or '/'
        return super(RequestStockMaterial, self).create(vals)

    def _prepare_stock_move_line(self, line, picking_type_id, picking_id):
        name = '[' + line.product_id.default_code + '] ' + line.product_id.name or ''
        company = self.env.user.company_id.id
        warehouse_id = self.warehouse_id
        var = {'picking_id': picking_id.id or False,
               #'name': name,
               'product_uom_id': line.product_id.uom_id.id or False,
               'init_qty': line.product_qty or 0.0,
               'qty_done': line.product_qty or 0.0,
               'price_unit': 0.0,
               'picking_type_id': picking_type_id.id or False,
               'location_id': picking_type_id.default_location_src_id.id or False,
               'location_dest_id': picking_type_id.default_location_dest_id.id or False,
               # 'date_expected': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT) or False,
               'partner_id': False,
               #'type': picking_type_id.code or False,
               #'scrapped': False,
               'company_id': company,
               'product_id': line.product_id.id or False,
               'date': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT) or False,
               'currency_id': False,
               'state': 'draft',
               'warehouse_id': warehouse_id.id or False,
               }
        return var

    def button_done(self):
        for this in self:
            crop_id = self.env['ned.crop'].search([('state', '=', 'current')], limit=1)
            var = {
                'crop_id':crop_id.id,
                'name': '/',
                'picking_type_id': self.picking_type_id.id,
                'origin': this.name,
                'scheduled_date': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT) or False,
                'date_done': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'partner_id': False,
                'picking_type_code': self.picking_type_id.code or False,
                'location_id': self.location_id.id or False,
                'location_dest_id': self.location_dest_id.id or False,
                'state': 'draft'
            }
            new_id = self.env['stock.picking'].create(var)
            this.picking_id = new_id.id
            for line in this.request_line_ids:
                if line.state == 'cancel':
                    continue
                move_line = self._prepare_stock_move_line(line, self.picking_type_id, new_id)
                move_id = self.env['stock.move.line'].create(move_line)
            this.state = 'done'


class RequestStockMaterialLine(models.Model):
    _name = 'request.stock.material.line'


    @api.onchange('product_id')
    def _onchange_product_id(self):
        for this in self:
            if this.product_id:
                this.name = this.product_id.product_tmpl_id.name or False
                this.product_uom = this.product_id.product_tmpl_id.uom_id or False

    product_id = fields.Many2one('product.product', string="Product")

    name = fields.Char(string='Name')

    product_uom = fields.Many2one('uom.uom', string="Uom")
    product_qty = fields.Float(string='Request Qty', default=0.0, digits=(12, 0))
    state = fields.Selection(related='request_id.state', string='State')

    request_id = fields.Many2one('request.stock.material', string="Request")


