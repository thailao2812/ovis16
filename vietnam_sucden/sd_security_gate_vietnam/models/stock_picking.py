# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from datetime import datetime, timedelta, time
import pytz


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    display_name = fields.Char(compute='_compute_display_name', compute_sudo=True)

    grn_ready_ids = fields.One2many('grn.ready', 'picking_id')
    grn_done_factory_ids = fields.One2many('grn.done.factory', 'picking_id')
    grn_done_fot_ids = fields.One2many('grn.done.fot', 'picking_id')

    allocated_request_payment = fields.Integer(string='Allocated Payment', compute='_compute_data_request_payment', store=True)
    remain_request_payment = fields.Integer(string='Remaining for Payment', compute='_compute_data_request_payment', store=True)

    @api.depends('grn_ready_ids', 'grn_done_factory_ids', 'grn_ready_ids.request_qty', 'grn_done_fot_ids', 'grn_done_fot_ids.request_qty',
                 'grn_done_factory_ids.request_qty', "total_init_qty", "state", "total_qty", 'picking_type_id', 'picking_type_id.operation')
    def _compute_data_request_payment(self):
        for rec in self:
            rec.allocated_request_payment = 0
            if rec.picking_type_id.operation != 'station':
                if rec.state == 'assigned':
                    rec.allocated_request_payment = sum(rec.grn_ready_ids.mapped('request_qty')) + sum(rec.grn_done_factory_ids.mapped('request_qty'))
                    rec.remain_request_payment = rec.total_init_qty - (sum(rec.grn_ready_ids.mapped('request_qty')) + sum(rec.grn_done_factory_ids.mapped('request_qty')))
                if rec.state == 'done':
                    rec.allocated_request_payment = sum(rec.grn_ready_ids.mapped('request_qty')) + sum(
                        rec.grn_done_factory_ids.mapped('request_qty'))
                    rec.remain_request_payment = rec.total_qty - (sum(rec.grn_ready_ids.mapped('request_qty')) + sum(
                        rec.grn_done_factory_ids.mapped('request_qty')))
            else:
                if rec.state == 'done':
                    rec.allocated_request_payment = sum(rec.grn_done_fot_ids.mapped('request_qty'))
                    rec.remain_request_payment = rec.total_qty - (sum(rec.grn_done_fot_ids.mapped('request_qty')))

    @api.depends('name', 'picking_type_id')
    def _compute_display_name(self):
        for sri in self:
            if sri.picking_type_id.operation == 'station':
                if sri.description_name:
                    sri.display_name = sri.description_name
                else:
                    sri.display_name = sri.name
            else:
                sri.display_name = sri.name

    def name_get(self):
        result = []
        for rec in self:
            if rec.picking_type_id.operation == 'station':
                if rec.description_name:
                    result.append((rec.id, rec.description_name))
                else:
                    result.append((rec.id, rec.name))
            else:
                result.append((rec.id, rec.name))
        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if self._context.get('allocation_grn'):
            if name:
                args += ['|', ('name', operator, name), ('description_name', operator, name)]
            backorder = self.search(args, limit=limit)
            return backorder.name_get()
        else:
            args = []
            domain = []
            check = []
            args += ['|', ('name', operator, name), ('description_name', operator, name)]
            backorder = self.search(args + domain, limit=limit)
            if self._context.get('grn_invoice'):
                purchase_contract = self.env['purchase.contract'].search([('id', '=', self._context.get('purchase_contract_id'))])
                stock_allocation = self.env['stock.allocation'].search([('contract_id', '=', purchase_contract.id)])
                domain += [('id', 'in', stock_allocation.mapped('picking_id').ids)]
                backorder = self.search(args + domain, limit=limit)
                return backorder.name_get()
            if self._context.get('grn_fot_allocation') and 'request_payment' not in self._context:
                if name:
                    args += ['|', ('name', operator, name), ('description_name', operator, name)]
                domain = args
                backorder = self.search(args + domain, limit=limit)
                return backorder.name_get()
            if self._context.get('back_order'):
                domain = [('picking_type_id.code', '=', 'incoming'),
                          ('picking_type_id.operation', '=', 'factory'),
                          ('partner_id', '=', self._context.get('partner_id')),
                          ('date_done', '>=', self._context.get('date_done')),
                          ('backorder_id', '=', False)]
                backorder = self.search(args + domain, limit=limit)
            if self._context.get('request_payment') and self._context.get('payment_percent') and self._context.get('seq'):
                grn_array = self._context.get('ids')
                if isinstance(grn_array, str):
                    grn_array = grn_array.strip('][').split(', ')
                    grn_array = [int(x) for x in grn_array if x.isdigit()]
                check += [('id', 'not in', grn_array)]
                if self._context.get('payment_percent') == 90:
                    check += [('warehouse_id', '=', self._context.get('warehouse_id')),
                                ('partner_id', '=', self._context.get('partner_id')),
                                ('state', 'not in', ['done', 'cancel', 'draft']),
                                ('picking_type_id.code', '=', 'incoming'),
                                ('picking_type_id.operation', '!=', 'station'),
                                ('name', '=like', 'GRN%'),
                                ('remain_request_payment', '>', 0),
                                ('date_done', '>=', self._context.get('date')),
                                ('product_id', '=', self._context.get('product_id'))]
                    grn_ids = self.search(args+check)
                    grn_ready = self.env['grn.ready'].search([
                        ('request_payment_id.name', '<', int(self._context.get('seq')))
                    ]).filtered(
                        lambda x: x.picking_id.id in grn_ids.ids
                    )
                    if grn_ready:
                        grn_ready_2nd = self.env['grn.ready'].search([
                            ('id', 'not in', grn_ready.ids)
                        ]).filtered(lambda x: x.picking_id.id in grn_ids.ids)
                    else:
                        grn_ready_2nd = self.env['grn.ready'].search([]).filtered(
                            lambda x: x.picking_id.id in grn_ids.ids)

                    arr_done = []
                    for i in grn_ready:
                        if i.remain_qty == 0:
                            if i.picking_id.id not in arr_done:
                                arr_done.append(i.picking_id.id)
                    for i in grn_ready_2nd:
                        if i.remain_qty == 0:
                            if i.picking_id.id not in arr_done:
                                arr_done.append(i.picking_id.id)
                    args += [('warehouse_id', '=', self._context.get('warehouse_id')),
                               ('partner_id', '=', self._context.get('partner_id')),
                                ('date_done', '>=', self._context.get('date')),('name', '=like', 'GRN%'),
                                ('picking_type_id.operation', '!=', 'station'),
                                ('remain_request_payment', '>', 0),
                               ('picking_type_id.code', '=', 'incoming'), ('id', 'not in', grn_array),
                                ('id', 'not in', arr_done), ('product_id', '=', self._context.get('product_id')),
                             ('state', 'not in', ['done', 'cancel', 'draft']), ('backorder_id', '=', False)]
                    backorder = self.search(args + domain, limit=limit)

                if self._context.get('payment_percent') == 100:
                    if self.env.context.get('factory'):
                        check += [('warehouse_id', '=', self._context.get('warehouse_id')),
                                  ('partner_id', '=', self._context.get('partner_id')),
                                  ('state', 'in', ['done']), ('name', '=like', 'GRN%'),
                                  ('date_done', '>=', self._context.get('date')),
                                  ('picking_type_id.operation', '!=', 'station'),
                                  ('picking_type_id.code', '=', 'incoming'),
                                  ('remain_request_payment', '>', 0),
                                  ('product_id', '=', self._context.get('product_id'))]
                        grn_ids = self.search(args + check)
                        grn_ready = self.env['grn.done.factory'].search([
                            ('request_payment_id.name', '<', int(self._context.get('seq')))
                        ]).filtered(
                            lambda x: x.picking_id.id in grn_ids.ids
                        )
                        if grn_ready:
                            grn_ready_2nd = self.env['grn.done.factory'].search([
                                ('id', 'not in', grn_ready.ids)
                            ]).filtered(lambda x: x.picking_id.id in grn_ids.ids)
                        else:
                            grn_ready_2nd = self.env['grn.done.factory'].search([]).filtered(
                                lambda x: x.picking_id.id in grn_ids.ids)

                        arr_done = []
                        for i in grn_ready:
                            if i.remain_qty == 0:
                                if i.picking_id.id not in arr_done:
                                    arr_done.append(i.picking_id.id)
                        for i in grn_ready_2nd:
                            if i.remain_qty == 0:
                                if i.picking_id.id not in arr_done:
                                    arr_done.append(i.picking_id.id)
                        args += [('warehouse_id', '=', self._context.get('warehouse_id')),
                                 ('partner_id', '=', self._context.get('partner_id')),
                                 ('date_done', '>=', self._context.get('date')), ('name', '=like', 'GRN%'),
                                 ('picking_type_id.code', '=', 'incoming'), ('id', 'not in', grn_array),
                                 ('picking_type_id.operation', '!=', 'station'),
                                 ('remain_request_payment', '>', 0),
                                 ('id', 'not in', arr_done), ('product_id', '=', self._context.get('product_id')),
                                 ('state', 'in', ['done']), ('backorder_id', '=', False)]
                        backorder = self.search(args + domain, limit=limit)
                    else:
                        check += [('warehouse_id.code', 'in', ['FA', 'KTN-LT-N', 'KTN-AP-N']),
                                  ('partner_id', '=', self._context.get('partner_id')),
                                  ('state', 'in', ['done']), ('name', '=like', 'GRN%'),
                                  ('date_done', '>=', self._context.get('date')),
                                  ('picking_type_id.operation', '=', 'station'),
                                  ('picking_type_id.code', '=', 'incoming'),
                                  ('remain_request_payment', '>', 0),
                                  ('product_id', '=', self._context.get('product_id'))]
                        grn_ids = self.search(args + check)
                        grn_ready = self.env['grn.done.fot'].search([
                            ('request_payment_id.name', '<', int(self._context.get('seq')))
                        ]).filtered(
                            lambda x: x.picking_id.id in grn_ids.ids
                        )
                        if grn_ready:
                            grn_ready_2nd = self.env['grn.done.fot'].search([
                                ('id', 'not in', grn_ready.ids)
                            ]).filtered(lambda x: x.picking_id.id in grn_ids.ids)
                        else:
                            grn_ready_2nd = self.env['grn.done.fot'].search([]).filtered(
                                lambda x: x.picking_id.id in grn_ids.ids)

                        arr_done = []
                        for i in grn_ready:
                            if i.remain_qty == 0:
                                if i.picking_id.id not in arr_done:
                                    arr_done.append(i.picking_id.id)
                        for i in grn_ready_2nd:
                            if i.remain_qty == 0:
                                if i.picking_id.id not in arr_done:
                                    arr_done.append(i.picking_id.id)
                        args += [('warehouse_id.code', 'in', ['FA', 'KTN-LT-N', 'KTN-AP-N']),
                                 ('partner_id', '=', self._context.get('partner_id')),
                                 ('picking_type_id.operation', '=', 'station'), ('name', '=like', 'GRN%'),
                                 ('date_done', '>=', self._context.get('date')),
                                 ('remain_request_payment', '>', 0),
                                 ('picking_type_id.code', '=', 'incoming'), ('id', 'not in', grn_array),
                                 ('id', 'not in', arr_done), ('product_id', '=', self._context.get('product_id')),
                                 ('state', 'in', ['done']), ('backorder_id', '=', False)]
                        backorder = self.search(args + domain, limit=limit)

            if self._context.get('picking_sample_ids'):
                domain = [('picking_type_id.code', '=', 'incoming'),
                          ('picking_type_id.operation', '=', 'factory'),
                          ('partner_id', '=', self._context.get('partner_id')),
                          ('use_sample','=', True),
                          ('kcs_sample_ids', '=', False), ('state_kcs', '=', 'draft'),
                          ('product_id', '=', self._context.get('product_id'))]

                user_tz = pytz.timezone(self.env.context.get('tz') or 'UTC')
                date = self._context.get('date')
                if date:
                    date = datetime.strptime(date, "%Y-%m-%d").date()
                    # Tạo datetime tại 00:00 và 23:59 trong TZ của user
                    local_start = user_tz.localize(datetime.combine(date, time.min))
                    local_end = user_tz.localize(datetime.combine(date + timedelta(days=1), time.min))

                    # Chuyển về UTC để so sánh với database
                    start_utc = local_start.astimezone(pytz.UTC)
                    end_utc = local_end.astimezone(pytz.UTC)
                    domain += [('date_done', '>=', start_utc), ('date_done', '<', end_utc)]
                backorder = self.search(args + domain, limit=limit)
        return backorder.name_get()

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        check = []
        if self._context.get('request_payment') and self._context.get('payment_percent') and self._context.get('seq'):
            grn_array = self._context.get('ids')
            if isinstance(grn_array, str):
                grn_array = grn_array.strip('][').split(', ')
                grn_array = [int(x) for x in grn_array if x.isdigit()]
            check += [('id', 'not in', grn_array)]
            if self._context.get('payment_percent') == 90:
                check += [('warehouse_id', '=', self._context.get('warehouse_id')),
                          ('partner_id', '=', self._context.get('partner_id')),
                          ('date_done', '>=', self._context.get('date')),
                          ('remain_request_payment', '>', 0),
                          ('picking_type_id.code', '=', 'incoming'), ('name', '=like', 'GRN%'),
                          ('picking_type_id.operation', '!=', 'station'),
                          ('product_id', '=', self._context.get('product_id')),
                          ('state', 'not in', ['done', 'cancel', 'draft'])]
                grn_ids = self.search(domain + check)
                grn_ready = self.env['grn.ready'].search([
                    ('request_payment_id.name', '<', int(self._context.get('seq')))
                ]).filtered(
                    lambda x: x.picking_id.id in grn_ids.ids
                )
                if grn_ready:
                    grn_ready_2nd = self.env['grn.ready'].search([
                        ('id', 'not in', grn_ready.ids)
                    ]).filtered(lambda x: x.picking_id.id in grn_ids.ids)
                else:
                    grn_ready_2nd = self.env['grn.ready'].search([]).filtered(
                        lambda x: x.picking_id.id in grn_ids.ids)

                arr_done = []
                for i in grn_ready:
                    if i.remain_qty == 0:
                        if i.picking_id.id not in arr_done:
                            arr_done.append(i.picking_id.id)
                for i in grn_ready_2nd:
                    if i.remain_qty == 0:
                        if i.picking_id.id not in arr_done:
                            arr_done.append(i.picking_id.id)
                domain += [('warehouse_id', '=', self._context.get('warehouse_id')),
                         ('partner_id', '=', self._context.get('partner_id')),
                           ('date_done', '>=', self._context.get('date')), ('name', '=like', 'GRN%'),
                         ('picking_type_id.code', '=', 'incoming'), ('id', 'not in', grn_array),
                           ('picking_type_id.operation', '!=', 'station'),
                           ('remain_request_payment', '>', 0),
                         ('id', 'not in', arr_done), ('product_id', '=', self._context.get('product_id')),
                         ('state', 'not in', ['done', 'cancel', 'draft']), ('backorder_id', '=', False)]
            if self._context.get('payment_percent') == 100:
                if self.env.context.get('factory'):
                    check += [('warehouse_id', '=', self._context.get('warehouse_id')),
                              ('partner_id', '=', self._context.get('partner_id')),
                              ('picking_type_id.operation', '=', 'factory'),
                              ('date_done', '>=', self._context.get('date')),
                              ('picking_type_id.operation', '!=', 'station'),
                              ('remain_request_payment', '>', 0),
                              ('picking_type_id.code', '=', 'incoming'), ('name', '=like', 'GRN%'),
                              ('product_id', '=', self._context.get('product_id')),
                              ('state', 'in', ['done'])]
                    grn_ids = self.search(domain + check)
                    grn_ready = self.env['grn.done.factory'].search([
                        ('request_payment_id.name', '<', int(self._context.get('seq')))
                    ]).filtered(
                        lambda x: x.picking_id.id in grn_ids.ids
                    )
                    if grn_ready:
                        grn_ready_2nd = self.env['grn.done.factory'].search([
                            ('id', 'not in', grn_ready.ids)
                        ]).filtered(lambda x: x.picking_id.id in grn_ids.ids)
                    else:
                        grn_ready_2nd = self.env['grn.done.factory'].search([]).filtered(
                            lambda x: x.picking_id.id in grn_ids.ids)

                    arr_done = []
                    for i in grn_ready:
                        if i.remain_qty == 0:
                            if i.picking_id.id not in arr_done:
                                arr_done.append(i.picking_id.id)
                    for i in grn_ready_2nd:
                        if i.remain_qty == 0:
                            if i.picking_id.id not in arr_done:
                                arr_done.append(i.picking_id.id)
                    domain += [('warehouse_id', '=', self._context.get('warehouse_id')),
                               ('partner_id', '=', self._context.get('partner_id')),
                               ('date_done', '>=', self._context.get('date')), ('name', '=like', 'GRN%'),
                               ('picking_type_id.code', '=', 'incoming'), ('id', 'not in', grn_array),
                               ('picking_type_id.operation', '!=', 'station'),
                               ('remain_request_payment', '>', 0),
                               ('id', 'not in', arr_done), ('product_id', '=', self._context.get('product_id')),
                               ('state', 'in', ['done']), ('backorder_id', '=', False)]
                else:
                    check += [('warehouse_id.code', 'in', ['FA', 'KTN-LT-N', 'KTN-AP-N']),
                              ('partner_id', '=', self._context.get('partner_id')),
                              ('picking_type_id.operation', '=', 'station'),
                              ('date_done', '>=', self._context.get('date')),
                              ('remain_request_payment', '>', 0),
                              ('picking_type_id.code', '=', 'incoming'), ('name', '=like', 'GRN%'),
                              ('product_id', '=', self._context.get('product_id')),
                              ('state', 'in', ['done'])]
                    grn_ids = self.search(domain + check)
                    grn_ready = self.env['grn.done.fot'].search([
                        ('request_payment_id.name', '<', int(self._context.get('seq')))
                    ]).filtered(
                        lambda x: x.picking_id.id in grn_ids.ids
                    )
                    if grn_ready:
                        grn_ready_2nd = self.env['grn.done.fot'].search([
                            ('id', 'not in', grn_ready.ids)
                        ]).filtered(lambda x: x.picking_id.id in grn_ids.ids)
                    else:
                        grn_ready_2nd = self.env['grn.done.fot'].search([]).filtered(
                            lambda x: x.picking_id.id in grn_ids.ids)

                    arr_done = []
                    for i in grn_ready:
                        if i.remain_qty == 0:
                            if i.picking_id.id not in arr_done:
                                arr_done.append(i.picking_id.id)
                    for i in grn_ready_2nd:
                        if i.remain_qty == 0:
                            if i.picking_id.id not in arr_done:
                                arr_done.append(i.picking_id.id)
                    domain += [('warehouse_id.code', 'in', ['FA', 'KTN-LT-N', 'KTN-AP-N']),
                               ('partner_id', '=', self._context.get('partner_id')),
                               ('picking_type_id.operation', '=', 'station'), ('name', '=like', 'GRN%'),
                               ('date_done', '>=', self._context.get('date')),
                               ('remain_request_payment', '>', 0),
                               ('picking_type_id.code', '=', 'incoming'), ('id', 'not in', grn_array),
                               ('id', 'not in', arr_done), ('product_id', '=', self._context.get('product_id')),
                               ('state', 'in', ['done']), ('backorder_id', '=', False)]
        return super(StockPicking, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit,
                                                     order=order)
