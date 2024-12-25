# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class DeliveryRegistration(models.Model):
    _inherit = 'ned.security.gate.queue'

    picking_ktn_id = fields.Many2one('stock.picking', string='GRN KTN Link')

    arrivial_time = fields.Datetime('Arrival Time', readonly=False)
    
    def _compute_my_field_readonly(self):
        self.block_request = self.env['res.users'].has_group('sd_purchase_contract.group_purchase_contract_user')

    block_request = fields.Boolean(default=False, string="Truck block request")
    weigh_block = fields.Boolean(default=False, string="Weigh & Block", readonly=True)

    @api.onchange('block_request')
    def _onchange_block_request(self):
        if self.block_request:
            if self.picking_ids and len(self.picking_ids)== 1:
                picking_id = self.picking_ids and self.picking_ids[0]
                if picking_id:
                    for move in picking_id.move_line_ids_without_package:
                        if move.first_weight > 0 and len(move) == 1 and picking_id.state == 'draft':
                            self.weigh_block = True
                            picks = self.env['stock.picking'].sudo().search([('vehicle_no','=',self.license_plate)], order='id desc')
                            for line in picks.move_line_ids_without_package:
                                if line.second_weight > 0 and len(move) == 1:
                                    self.approx_quantity = round(move.first_weight - line.second_weight, -3)
                                    break
        else:
            self.weigh_block = False

    def button_link_grn_ktn(self):
        for rec in self:
            if rec.picking_ktn_id:
                if rec.picking_ktn_id.security_gate_id:
                    raise UserError(_("This GRN already linked to DR %s") % rec.picking_ktn_id.security_gate_id.name)
                else:
                    rec.picking_ktn_id.security_gate_id = rec.id
            else:
                return True

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            args += [('name', operator, name)]
        delivery_registration = self.search(args + domain, limit=limit)
        if self._context.get('request_payment'):
            try:
                if self._context.get('delivery_factory'):
                    product = self.env['product.product'].browse(self._context.get('product_id'))
                    deliver_array = self._context.get('ids')
                    if isinstance(deliver_array, str):
                        deliver_array = deliver_array.strip('][').split(', ')
                        deliver_array = [int(x) for x in deliver_array if x.isdigit()]
                    delivery_temp_ids = self.search([
                        ('type_transfer', '=', 'queue'),
                        ('state', 'not in', ['cancel', 'closed', 'reject']),
                        ('supplier_id', '=', self._context.get('partner_id')),
                        ('id', 'not in', deliver_array)
                    ], limit=limit).filtered(
                        lambda x: product.id in x.product_ids.ids)
                    delivery_ready = self.env['delivery.ready'].search([
                        ('request_payment_id.name', '<', int(self._context.get('seq')))
                    ]).filtered(
                        lambda x: x.delivery_id.id in delivery_temp_ids.ids
                    )
                    arr_done = []
                    for i in delivery_ready:
                        if i.remain_qty == 0:
                            arr_done.append(i.delivery_id.id)
                    args += [('type_transfer', '=', 'queue'),
                        ('state', 'not in', ['cancel', 'closed', 'reject']),
                        ('supplier_id', '=', self._context.get('partner_id')),
                        ('id', 'not in', deliver_array),
                        ('arrivial_time', '<=', self._context.get('date')),
                        ('id', 'not in', arr_done), ('product_ids', 'in', product.id)]
                    delivery_registration = self.search(domain+args, limit=limit)

                if self._context.get('delivery_ktn'):
                    product = self.env['product.product'].browse(self._context.get('product_id'))
                    deliver_array = self._context.get('ids')
                    if isinstance(deliver_array, str):
                        deliver_array = deliver_array.strip('][').split(', ')
                        deliver_array = [int(x) for x in deliver_array if x.isdigit()]
                    delivery_temp_ids = self.search([
                        ('type_transfer', '=', 'other'),
                        ('supplier_id', '=', self._context.get('partner_id')),
                        ('id', 'not in', deliver_array)
                    ], limit=limit).filtered(
                        lambda x: product.id in x.product_ids.ids)
                    delivery_ready = self.env['delivery.ktn'].search([
                        ('request_payment_id.name', '<', int(self._context.get('seq')))
                    ]).filtered(
                        lambda x: x.delivery_id.id in delivery_temp_ids.ids
                    )
                    arr_done = []
                    for i in delivery_ready:
                        if i.remain_qty == 0:
                            arr_done.append(i.delivery_id.id)
                    args += [('type_transfer', '=', 'other'),
                        ('supplier_id', '=', self._context.get('partner_id')),
                        ('id', 'not in', deliver_array),
                        ('picking_ktn_id', '=', False),
                        ('arrivial_time', '<=', self._context.get('date')),
                        ('id', 'not in', arr_done), ('product_ids', 'in', product.id)]
                    delivery_registration = self.search(domain+args, limit=limit)
            except ValidationError as e:
                raise UserError(_("Invalid field input : %s") % e.args)
            return delivery_registration.name_get()
        return delivery_registration.name_get()

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if self._context.get('request_payment'):
            if self._context.get('delivery_factory'):
                product = self.env['product.product'].browse(self._context.get('product_id'))
                deliver_array = self._context.get('ids')
                if isinstance(deliver_array, str):
                    deliver_array = deliver_array.strip('][').split(', ')
                    deliver_array = [int(x) for x in deliver_array if x.isdigit()]
                delivery_temp_ids = self.search([
                    ('type_transfer', '=', 'queue'),
                    ('state', 'not in', ['cancel', 'closed', 'reject']),
                    ('supplier_id', '=', self._context.get('partner_id')),
                    ('id', 'not in', deliver_array)
                ], limit=limit).filtered(
                    lambda x: product.id in x.product_ids.ids)
                delivery_ready = self.env['delivery.ready'].search([
                    ('request_payment_id.name', '<', int(self._context.get('seq')))
                ]).filtered(
                    lambda x: x.delivery_id.id in delivery_temp_ids.ids
                )
                arr_done = []
                for i in delivery_ready:
                    if i.remain_qty == 0:
                        arr_done.append(i.delivery_id.id)

                domain += [
                    ('type_transfer', '=', 'queue'),
                    ('state', 'not in', ['cancel', 'closed', 'reject']),
                    ('supplier_id', '=', self._context.get('partner_id')),
                    ('id', 'not in', deliver_array),
                    ('arrivial_time', '<=', self._context.get('date')),
                    ('id', 'not in', arr_done), ('product_ids', 'in', product.id)]

            if self._context.get('delivery_ktn'):
                product = self.env['product.product'].browse(self._context.get('product_id'))
                deliver_array = self._context.get('ids')
                if isinstance(deliver_array, str):
                    deliver_array = deliver_array.strip('][').split(', ')
                    deliver_array = [int(x) for x in deliver_array if x.isdigit()]
                delivery_temp_ids = self.search([
                    ('type_transfer', '=', 'other'),
                    ('supplier_id', '=', self._context.get('partner_id')),
                    ('id', 'not in', deliver_array)
                ], limit=limit).filtered(
                    lambda x: product.id in x.product_ids.ids)
                delivery_ready = self.env['delivery.ktn'].search([
                    ('request_payment_id.name', '<', int(self._context.get('seq')))
                ]).filtered(
                    lambda x: x.delivery_id.id in delivery_temp_ids.ids
                )
                arr_done = []
                for i in delivery_ready:
                    if i.remain_qty == 0:
                        arr_done.append(i.delivery_id.id)

                domain += [
                    ('type_transfer', '=', 'other'),
                    ('supplier_id', '=', self._context.get('partner_id')),
                    ('id', 'not in', deliver_array),
                    ('picking_ktn_id', '=', False),
                    ('arrivial_time', '<=', self._context.get('date')),
                    ('id', 'not in', arr_done), ('product_ids', 'in', product.id)]
        return super(DeliveryRegistration, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit,
                                                     order=order)
