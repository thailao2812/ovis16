# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class DeliveryRegistration(models.Model):
    _inherit = 'ned.security.gate.queue'

    picking_ktn_id = fields.Many2one('stock.picking', string='GRN KTN Link')

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
                        ('state', 'not in', ['approved', 'cancel', 'closed', 'reject']),
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
                        ('state', 'not in', ['approved', 'cancel', 'closed', 'reject']),
                        ('supplier_id', '=', self._context.get('partner_id')),
                        ('id', 'not in', deliver_array),
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
                    ('state', 'not in', ['approved', 'cancel', 'closed', 'reject']),
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
                    ('state', 'not in', ['approved', 'cancel', 'closed', 'reject']),
                    ('supplier_id', '=', self._context.get('partner_id')),
                    ('id', 'not in', deliver_array),
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
                    ('id', 'not in', arr_done), ('product_ids', 'in', product.id)]
        return super(DeliveryRegistration, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit,
                                                     order=order)
