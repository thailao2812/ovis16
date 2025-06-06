# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    lot_kcs_id = fields.Many2one('lot.kcs', string="Lot")

class LotKcsInherit(models.Model):
    _inherit = "lot.kcs"
    _description = 'Lot Management'
    _name = "lot.kcs"  # Không cần khai báo lại nếu chỉ thêm mixin
    _inherit = ["lot.kcs", "mail.thread", "mail.activity.mixin"]

    def action_view_picking(self):
        result = self.env['ir.actions.act_window']._for_xml_id('sd_inventory.action_gdns_good')
        res = self.env.ref('sd_inventory.view_picking_form_gdn_good', False)
        form_view = [(res and res.id or False, 'form')]
        if 'views' in result:
            result['views'] = form_view + [(state, view) for state, view in result['views'] if view != 'form']
        else:
            result['views'] = form_view
        result['res_id'] = self.picking_id.id

        return result

    picking_id = fields.Many2one('stock.picking', string="GDN", readonly=True)

    @api.depends('picking_id')
    def _compute_count_picking(self):
        for order in self:
            if order.picking_id:
                order.picking_count = 1
            else:
                order.picking_count = 0

    picking_count = fields.Integer(compute='_compute_count_picking', string='Delivery', default=0)
    los_ids = fields.One2many('lot.stack.allocation', 'lot_id', string="Lot Allocation", readonly=False)
    state = fields.Selection([('draft', 'Draft'), ('ready', 'Ready to Weight'), ('approve', 'Approve')], string="State", required=True, default="draft")
    # nvs_id = fields.Many2one('sale.contract', string="NVS - Nls", readonly=False, domain="[('scontract_id', '=', contract_id)]")
    nvs_nls_ids = fields.Many2many('sale.contract', 'lot_kcs_sale_contract_rel', 'lot_id', 'contract_id', string='NVS - NLS', 
                            readonly=True)
    delivery_ids = fields.Many2many('delivery.order', 'lot_kcs_delivery_order_rel', 'lot_id', 'delivery_id', string="Do No.", 
                            readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse") #, compute='_compute_warehouse_id'
    qty_delivery = fields.Float(related='delivery_id.total_qty', string='Qty Delivery', store=True)
    shipping_id = fields.Many2one('shipping.instruction', string='SI No.', ondelete='cascade', readonly=True, required=True, states={'draft': [('readonly', False)],'ready': [('readonly', False)]})
    si_qty = fields.Float(related='shipping_id.total_line_qty', string='SI Qty.', store=True)

    vehicle_no = fields.Char(string="Truck No")
    trucking_id = fields.Many2one('res.partner', string="Trucking Co.")
    first_cont = fields.Char(string='First Container')
    last_cont = fields.Char(string='Last Container')
    seal = fields.Char(string="Seal")

    # @api.onchange('shipping_id', 'security_gate_id')
    # def _onchange_shipping_id(self):
    #     for this in self:
    #         if this.shipping_id and this.security_gate_id:
    #             this.vehicle_no = this.security_gate_id.license_plate
    #             this.trucking_id = this.security_gate_id.trucking_id.id
    #             this.first_cont = this.security_gate_id.first_cont
    #             this.last_cont = this.security_gate_id.last_cont
    #             this.contract_id = this.shipping_id.contract_id.id
    #             this.nvs_nls_ids = this.security_gate_id.nvs_nls_id.ids
    #             this.delivery_ids = this.security_gate_id.delivery_id.ids
    #         else:
    #             return True
            
    gate_id = fields.Many2one('ned.security.gate.queue','Security Gate')

    # @api.onchange('shipping_id')
    # def _onchange_shipping_id(self):
    #     self.vehicle_no = False
    #     self.trucking_id = False
    #     self.first_cont = False
    #     self.last_cont = False
    #     if self.shipping_id:
    #         print("onchange shipping_id", self.shipping_id.gate_ids.ids)
    #         queue = self.env['ned.security.gate.queue'].search(
    #             [('shipping_id', '=', self.shipping_id.id),('state', '=', 'approved')],
    #             limit=1
    #         )
    #         if queue:
    #             print(queue.nvs_nls_id.ids, queue.delivery_id.ids)
    #             self.vehicle_no = queue.license_plate
    #             self.trucking_id = queue.trucking_id.id
    #             self.first_cont = queue.first_cont
    #             self.last_cont = queue.last_cont
    #             self.contract_id = self.shipping_id.contract_id.id
    #             self.nvs_nls_ids = queue.nvs_nls_id.ids
    #             self.delivery_ids = queue.delivery_id.ids

    # @api.depends('x_ex_warehouse_id')
    # def _compute_warehouse_id(self):
    #     for this in self:
    #         if this.x_ex_warehouse_id and this.x_ex_warehouse_id.x_name:
    #             get_warehouse = self.env['stock.warehouse'].search([('code', '=', this.x_ex_warehouse_id.x_name)], limit=1)
    #             this.warehouse_id = get_warehouse.id

    # @api.onchange('delivery_id')
    # def onchange_delivery(self):
    #     if self.delivery_id:

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        warehouse_ids = self.env['stock.warehouse'].with_context(user_workers=True).search(
            [('company_id', '=', self.env.user.company_id.id)], limit =1)
        if warehouse_ids:
            res['warehouse_id'] = warehouse_ids.ids[0]
        return res

    def btt_draft(self):
        for this in self:
            this.state = 'draft'
            if this.picking_id.state == 'done':
                error = '''You can not Set to Draft, Picking %s is  done''' % this.picking_id.name
                raise UserError(_(error))
            for j in this.los_ids:
                move_line = self.env['stock.move.line'].search([('lot_kcs_id', '=', this.id)])
                if move_line.picking_id.state == 'done':
                    error = '''You can not Set to Draft, Picking %s is  done''' % this.picking_id.name
                    raise UserError(_(error))
                move_line.unlink()
            this.picking_id = False

    def unlink(self):
        for i in self:
            if i.state != 'draft':
                raise UserError(_('You cannot delete records of this model!'))
        return super(LotKcs, self).unlink()

    def get_qc(self):
        # Gọi lại logic cũ
        super().get_qc()
        # Cập nhật lot_date: cập nhật với mỗi record trong self
        for record in self:
            record.lot_date = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        return True

    def btt_ready(self):
        for this in self:
            this.state = 'ready'
            if not this.los_ids:
                error = '''Không thể Ready to Weight khi chưa có thông tin của Line Allocated'''
                raise UserError(_(error))

            for i in this.los_ids:
                if round(i.stack_id.init_qty, 3) < round(i.quantity, 3):
                    error = '''You can not Ready to Weight, %s Inventory quantity is less than Quantity Allocated ''' % i.stack_id.name
                    raise UserError(_(error))
                
    def btt_confirm(self):
        for this in self:
            this.state = 'approve'
            # Kiệt check điều kiện duyệt

            if not this.los_ids:
                error = '''Không thể Confirm Lot Manager, Chưa có thông tin của Line thông tin sản phẩm '''
                raise UserError(_(error))

            for i in this.los_ids:
                if round(i.stack_id.init_qty, 3) < round(i.quantity, 3):
                    error = '''You can not Confirm, %s Inventory quantity is less than Quantity Allocated ''' % i.stack_id.name
                    raise UserError(_(error))


            if this.delivery_id:
                packing_id = False
                for q in this.stack_id.move_line_ids:
                    if q.location_id.usage == 'production' and q.location_dest_id.usage == 'internal':
                        if q.packing_id:
                            packing_id = q.packing_id.id

                if this.delivery_id.type == 'Sale':
                    warehouse = this.warehouse_id
                    if this.nvs_id.type != 'local':
                        picking_type_id = warehouse.out_type_id
                    else:
                        picking_type_id = warehouse.out_type_local_id

                    gdn_id = self.env['stock.picking'].search(
                        [('delivery_id', '=', this.delivery_id.id), ('state', '!=', 'done')]) or False
                    if not gdn_id:
                        var = {'name': '/',
                               'picking_type_id': picking_type_id.id or False,
                               'scheduled_date': datetime.now(),
                               'origin': 'S Contract ' + this.contract_id.name + ' - ' + this.nvs_id.name or '',
                               'partner_id': this.delivery_id.partner_id.id or False,
                               'picking_type_code': picking_type_id.code or False,
                               'location_id': warehouse.lot_stock_id.id or False,
                               'vehicle_no':this.delivery_id.trucking_no or '',
                               'location_dest_id': picking_type_id.default_location_dest_id.id or False,
                               'delivery_id': this.delivery_id.id,
                               'date_done': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                               }
                        new_picking_id = self.env['stock.picking'].create(var)
                        gdn_id = new_picking_id
                        this.delivery_id.picking_id = new_picking_id.id

                    for line in this.los_ids:
                        line.gdn_id = gdn_id.id
                        line.nvs_id = this.nvs_id.id
                        line.delivery_id = this.delivery_id.id
                        line.vehicle_no = this.delivery_id.trucking_no or ''
                        line.state = 'approve'
                        if not packing_id:
                            packing_id = line.packing_id.id
                        self.env['stock.move.line'].create({'picking_id': gdn_id.id or False,
                                'product_id': this.product_id.id or False,
                                'product_uom_id': this.product_id.uom_id.id or False,
                                'init_qty': line.quantity or 0.0,
                                'bag_no': line.no_of_bag or 0,
                                'price_unit': 0.0,
                                'picking_type_id': picking_type_id.id or False,
                                'location_id': picking_type_id.default_location_src_id.id or False,
                                'date': datetime.now(),
                                'location_dest_id': picking_type_id.default_location_dest_id.id or False,
                                'partner_id': this.partner_id.id or False,
                                'company_id': 1,
                                'state': 'draft',
                                'packing_id':packing_id or False,
                                'zone_id': line.zone_id.id,
                                'lot_id': line.stack_id.id,
                                'lot_kcs_id':this.id,

                                'warehouse_id': warehouse.id or False})
                    this.picking_id = gdn_id.id
        
# class ShippingInstruction(models.Model):
#     _inherit = 'shipping.instruction'

#     gate_ids = fields.One2many('ned.security.gate.queue','shipping_id', string='Security Gate Queue')

