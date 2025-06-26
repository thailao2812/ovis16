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
        action = self.env.ref('sd_inventory.action_gdns_good')
        result = action.read()[0]
        pick_ids = sum([order.gdn_id.ids for order in self.los_ids], [])
        if len(pick_ids) > 1:
            result['domain'] = "[('id','in',[" + ','.join(map(str, pick_ids)) + "])]"
        elif len(pick_ids) == 1:
            res = self.env.ref('sd_inventory.view_picking_form_gdn_good', False)
            result['context'] = {}
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = pick_ids and pick_ids[0] or False
        return result

    picking_ids = fields.Many2many('stock.picking', string="GDN", readonly=True)

    @api.depends('los_ids.gdn_id')
    def _compute_count_picking(self):
        for rec in self:
            gdn_ids = [los.gdn_id.id for los in rec.los_ids if los.gdn_id]
            unique_gdn_ids = set(gdn_ids)
            rec.picking_count = len(unique_gdn_ids)

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
    si_id = fields.Many2one('shipping.instruction', string='SI No.', ondelete='cascade', readonly=True, required=True, states={'draft': [('readonly', False)],'ready': [('readonly', False)]})
    si_qty = fields.Float(related='si_id.total_line_qty', string='SI Qty.', store=True)

    vehicle_no = fields.Char(string="Truck No")
    trucking_id = fields.Many2one('res.partner', string="Trucking Co.")
    first_cont = fields.Char(string='First Container')
    last_cont = fields.Char(string='Last Container')
    seal = fields.Char(string="Seal")

    security_gate_id = fields.Many2one('ned.security.gate.queue','Security Gate', required=False)
    mc_on_despatch = fields.Float(compute='_compute_mc_on_despatch',string="Mc On Despatch",  digits=(12, 2),store=True, tracking=True)
    defects_tcvn = fields.Float(string="Defects-TCVN", digits=(12, 2), tracking=True)
    defects = fields.Float(string="Defects-ISO", digits=(12, 2), tracking=True)
    fixed_black = fields.Float(string="Black", digits=(12, 2), tracking=True)
    fixed_broken = fields.Float(string="Broken", digits=(12, 2), tracking=True)
    fixed_brown = fields.Float(string="Brown", digits=(12, 2), tracking=True) 
    fixed_mold = fields.Float(string="Mold", digits=(12, 2), tracking=True) 


    @api.onchange('si_id', 'security_gate_id', 'los_ids')
    def _onchange_si_id(self):
        for rec in self:
            total = sum(line.quantity for line in rec.los_ids)
            if total > 28000:
                raise ValidationError(_('The total quantity across all LOT exceeds 28,000!'))

        if self.si_id:
            self.contract_id = self.si_id.contract_id.id
            self.partner_id = self.si_id.partner_id.id
            if self.security_gate_id:
                self.vehicle_no = self.security_gate_id.license_plate
                self.trucking_id = self.security_gate_id.trucking_id.id
                self.first_cont = self.security_gate_id.first_cont
                self.last_cont = self.security_gate_id.last_cont
                self.nvs_nls_ids = self.security_gate_id.nvs_nls_id.ids
                self.delivery_ids = self.security_gate_id.delivery_id.ids
            else:
                delivery_ids = self.los_ids.mapped('delivery_id').ids
                contract_ids = self.los_ids.mapped('delivery_id.contract_id').ids
                delivery_ids = list(set(delivery_ids))
                contract_ids = list(set(contract_ids))
                self.delivery_ids = [(6, 0, delivery_ids)]
                self.nvs_nls_ids = [(6, 0, contract_ids)]

            if self.delivery_ids and not self.security_gate_id:
                self.nvs_id = self.delivery_ids[0].contract_id.id
                self.vehicle_no = self.delivery_ids[0].trucking_no or False
                self.trucking_id = self.delivery_ids[0].trucking_id.id or False
                self.first_cont = False
                self.last_cont = False

    # @api.depends('x_ex_warehouse_id')
    # def _compute_warehouse_id(self):
    #     for this in self:
    #         if this.x_ex_warehouse_id and this.x_ex_warehouse_id.x_name:
    #             get_warehouse = self.env['stock.warehouse'].search([('code', '=', this.x_ex_warehouse_id.x_name)], limit=1)
    #             this.warehouse_id = get_warehouse.id

    @api.onchange('warehouse_id')
    def onchange_warehouse_id(self):
        if self.warehouse_id:
            external_wh = self.env['x_external.warehouse'].search([('name', '=', self.warehouse_id.code)], limit=1)
            self.x_ex_warehouse_id = external_wh.id

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        warehouse_ids = self.env['stock.warehouse'].with_context(user_workers=True).search(
            [('company_id', '=', self.env.user.company_id.id)], limit =1)
        if warehouse_ids:
            res['warehouse_id'] = warehouse_ids.ids[0]
        return res

    def btt_draft(self):
        for gdn in self.picking_ids:
            if gdn.state == 'done':
                error = '''You can not Set to Draft, Picking %s is  done''' % gdn.name
                raise UserError(_(error))
        self.picking_ids = False
        self.state = 'draft'
        self.lot_date = False

        for j in self.los_ids:
            move_line = self.env['stock.move.line'].search([('lot_kcs_id', '=', self.id),('lot_id', '=', j.stack_id.id),('picking_id', '=', j.gdn_id.id)])
            if move_line.picking_id.state == 'done':
                error = '''You can not Set to Draft, Picking %s is done''' % move_line.picking_id.name
                raise UserError(_(error))
            move_line.unlink()
        

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

    @api.depends('mc_on_despatch','defects','defects_tcvn')
    def _compute_mc_on_despatch(self):
        # Kế thừa lại để bỏ qua logic gốc, vì mc_on_despatch và defects trong hàm này
        # đang được tính theo trung bình cộng => sai logic.
        pass

    @api.onchange('mc_on_despatch','defects','defects_tcvn','cuptaste')
    def _onchange_mc_on_despatch(self):
        for rec in self:
            if rec.los_ids:
                for lot in rec.los_ids:
                    # Đảm bảo các field này có tồn tại trong model của los_ids
                    lot.mc_on_despatch = rec.mc_on_despatch
                    lot.defects = rec.defects
                    lot.defects_tcvn = rec.defects_tcvn
                    lot.cuptaste = rec.cuptaste

    def btt_ready(self):
        self.state = 'ready'
        if not self.lot_date:
            error = '''Can not Ready to Weight when you are not click LOAD QC'''
            raise UserError(_(error))
        if not self.los_ids:
            error = '''Can not Ready to Weight because line of Lot Allocate is empty!!!'''
            raise UserError(_(error))

        for i in self.los_ids:
            if round(i.stack_id.init_qty, 3) < round(i.quantity, 3):
                error = '''You can not Ready to Weight, %s Inventory quantity is less than Quantity Allocated ''' % i.stack_id.name
                raise UserError(_(error))

        # if self.delivery_ids[0].type == 'Sale':
        #     warehouse = self.warehouse_id
        #     if self.nvs_nls_ids[0].type != 'local':
        #         picking_type_id = warehouse.out_type_id
        #     else:
        #         picking_type_id = warehouse.out_type_local_id

        StockPicking = self.env['stock.picking']
        StockMoveLine = self.env['stock.move.line']

        for lot in self.los_ids:
            if not lot.stack_id:
                error = '''Please input Stack before confirm this Lot Allocation!!!'''
                raise UserError(_(error))
            
            no_of_bag = lot.stack_id.bag_qty
            if no_of_bag > 0:
                total_bags = sum(self.los_ids.filtered(lambda x: x.stack_id == lot.stack_id).mapped('no_of_bag'))
                if total_bags > no_of_bag:
                    raise UserError(_("Stack: %s have only %s\n"
                                      "But you are input total %s > %s of Stack, please check no of bag again")
                                    % (lot.stack_id.name, no_of_bag, total_bags, no_of_bag))
                if lot.no_of_bag < 0:
                    raise UserError(_("Cannot input no of bag < 0!!!"))
                if lot.quantity <= 0:
                    raise UserError(_("Cannot input quantity <= 0!!!"))

            if lot.delivery_id:
                packing_id = False
                for q in lot.stack_id.move_line_ids:
                    if q.location_id.usage == 'production' and q.location_dest_id.usage == 'internal':
                        if q.packing_id:
                            packing_id = q.packing_id.id
            
                if lot.delivery_id.type == 'Sale':
                    warehouse = self.warehouse_id
                    if lot.nvs_id.type != 'local':
                        picking_type_id = warehouse.out_type_id
                    else:
                        picking_type_id = warehouse.out_type_local_id

                    if not picking_type_id:
                        raise UserError(_('Need to define Picking Type for this transaction'))

                    if not lot.delivery_id.picking_id:
                        gdn_vals = {'name': '/',
                                'picking_type_id': picking_type_id.id or False,
                                'scheduled_date': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                                'origin': 'S Contract ' + self.si_id.name + ' - ' + lot.delivery_id.contract_id.name or '',
                                'partner_id': self.partner_id.id or False,
                                'picking_type_code': picking_type_id.code or False,
                                'location_id': warehouse.lot_stock_id.id or False,
                                'vehicle_no': lot.delivery_id.trucking_no or '',
                                'location_dest_id': picking_type_id.default_location_dest_id.id or False,
                                'delivery_id': lot.delivery_id.id,
                                'date_done': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                               }
                        picking_id = StockPicking.create(gdn_vals)
                        lot.delivery_id.picking_id = picking_id.id
                    else:
                        picking_id = lot.delivery_id.picking_id

                    if not lot.gdn_id:
                        lot.gdn_id = picking_id.id

                    sml_vals = {
                        'picking_id': picking_id.id or False,
                        'product_id': lot.product_id.id or False,
                        'product_uom_id': lot.product_id.uom_id.id or False,
                        'init_qty': lot.quantity or 0.0,
                        'bag_no': lot.no_of_bag or 0,
                        'price_unit': 0.0,
                        'picking_type_id': picking_type_id.id or False,
                        'location_id': picking_type_id.default_location_src_id.id or False,
                        'date': datetime.now(),
                        'location_dest_id': picking_type_id.default_location_dest_id.id or False,
                        'partner_id': self.partner_id.id or False,
                        'company_id': 1,
                        'state': 'draft',
                        'packing_id': lot.packing_id.id or False,
                        'zone_id': lot.zone_id.id,
                        'lot_id': lot.stack_id.id,
                        'lot_kcs_id': self.id,
                        'warehouse_id': warehouse.id or False
                    }
                    StockMoveLine.create(sml_vals)
                    lot.state = 'approve'

        # for delivery in self.delivery_ids:
        #     gdn_id = StockPicking.search(
        #         [('delivery_id', '=', delivery.id), ('state', '!=', 'done')], limit=1
        #     )
        #     if not gdn_id:
        #         gdn_vals = {'name': '/',
        #             'picking_type_id': picking_type_id.id or False,
        #             'scheduled_date': datetime.now(),
        #             'origin': 'S Contract ' + self.si_id.name + ' - ' + delivery.contract_id.name or '',
        #             'partner_id': self.partner_id.id or False,
        #             'picking_type_code': picking_type_id.code or False,
        #             'location_id': warehouse.lot_stock_id.id or False,
        #             'vehicle_no':self.vehicle_no or '',
        #             'location_dest_id': picking_type_id.default_location_dest_id.id or False,
        #             'delivery_id': delivery.id,
        #             'date_done': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        #             }
        #         gdn_id = StockPicking.create(gdn_vals)

        #         delivery_lines = self.los_ids.filtered(lambda l: l.delivery_id.id == delivery.id)
        #         for line in delivery_lines:
        #             line.gdn_id = gdn_id.id
        #             line.state = 'approve'
        #             sml_vals = {
        #                 'picking_id': gdn_id.id or False,
        #                 'product_id': self.product_id.id or False,
        #                 'product_uom_id': self.product_id.uom_id.id or False,
        #                 'init_qty': line.quantity or 0.0,
        #                 'bag_no': line.no_of_bag or 0,
        #                 'price_unit': 0.0,
        #                 'picking_type_id': picking_type_id.id or False,
        #                 'location_id': picking_type_id.default_location_src_id.id or False,
        #                 'date': datetime.now(),
        #                 'location_dest_id': picking_type_id.default_location_dest_id.id or False,
        #                 'partner_id': self.partner_id.id or False,
        #                 'company_id': 1,
        #                 'state': 'draft',
        #                 'packing_id': line.packing_id.id or False,
        #                 'zone_id': line.zone_id.id,
        #                 'lot_id': line.stack_id.id,
        #                 'lot_kcs_id': self.id,
        #                 'warehouse_id': warehouse.id or False
        #             }
        #             StockMoveLine.create(sml_vals)

        gdn_ids = self.los_ids.mapped('gdn_id')
        self.picking_ids = [(6, 0, gdn_ids.ids)]

    def btt_confirm(self):
        for this in self:
            this.state = 'approve'
            # # Kiệt check điều kiện duyệt
            #
            # if not this.los_ids:
            #     error = '''Không thể Confirm Lot Manager, Chưa có thông tin của Line thông tin sản phẩm '''
            #     raise UserError(_(error))
            #
            # for i in this.los_ids:
            #     if round(i.stack_id.init_qty, 3) < round(i.quantity, 3):
            #         error = '''You can not Confirm, %s Inventory quantity is less than Quantity Allocated ''' % i.stack_id.name
            #         raise UserError(_(error))
            #
            #
            # if this.delivery_id:
            #     packing_id = False
            #     for q in this.stack_id.move_line_ids:
            #         if q.location_id.usage == 'production' and q.location_dest_id.usage == 'internal':
            #             if q.packing_id:
            #                 packing_id = q.packing_id.id
            #
            #     if this.delivery_id.type == 'Sale':
            #         warehouse = this.warehouse_id
            #         if this.nvs_id.type != 'local':
            #             picking_type_id = warehouse.out_type_id
            #         else:
            #             picking_type_id = warehouse.out_type_local_id
            #
            #         gdn_id = self.env['stock.picking'].search(
            #             [('delivery_id', '=', this.delivery_id.id), ('state', '!=', 'done')]) or False
            #         if not gdn_id:
            #             var = {'name': '/',
            #                    'picking_type_id': picking_type_id.id or False,
            #                    'scheduled_date': datetime.now(),
            #                    'origin': 'S Contract ' + this.contract_id.name + ' - ' + this.nvs_id.name or '',
            #                    'partner_id': this.delivery_id.partner_id.id or False,
            #                    'picking_type_code': picking_type_id.code or False,
            #                    'location_id': warehouse.lot_stock_id.id or False,
            #                    'vehicle_no':this.delivery_id.trucking_no or '',
            #                    'location_dest_id': picking_type_id.default_location_dest_id.id or False,
            #                    'delivery_id': this.delivery_id.id,
            #                    'date_done': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            #                    }
            #             new_picking_id = self.env['stock.picking'].create(var)
            #             gdn_id = new_picking_id
            #             this.delivery_id.picking_id = new_picking_id.id
            #
            #         for line in this.los_ids:
            #             line.gdn_id = gdn_id.id
            #             # line.nvs_id = this.nvs_id.id
            #             # line.delivery_id = this.delivery_id.id
            #             # line.vehicle_no = this.delivery_id.trucking_no or ''
            #             line.state = 'approve'
            #             if not packing_id:
            #                 packing_id = line.packing_id.id
            #             self.env['stock.move.line'].create({'picking_id': gdn_id.id or False,
            #                     'product_id': this.product_id.id or False,
            #                     'product_uom_id': this.product_id.uom_id.id or False,
            #                     'init_qty': line.quantity or 0.0,
            #                     'bag_no': line.no_of_bag or 0,
            #                     'price_unit': 0.0,
            #                     'picking_type_id': picking_type_id.id or False,
            #                     'location_id': picking_type_id.default_location_src_id.id or False,
            #                     'date': datetime.now(),
            #                     'location_dest_id': picking_type_id.default_location_dest_id.id or False,
            #                     'partner_id': this.partner_id.id or False,
            #                     'company_id': 1,
            #                     'state': 'draft',
            #                     'packing_id':packing_id or False,
            #                     'zone_id': line.zone_id.id,
            #                     'lot_id': line.stack_id.id,
            #                     'lot_kcs_id':this.id,
            #
            #                     'warehouse_id': warehouse.id or False})
            #         this.picking_id = gdn_id.id
