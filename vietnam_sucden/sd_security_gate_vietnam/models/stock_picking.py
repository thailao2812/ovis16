# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    display_name = fields.Char(compute='_compute_display_name', compute_sudo=True)

    @api.depends('name', 'picking_type_id')
    def _compute_display_name(self):
        for sri in self:
            if sri.picking_type_id.operation == 'station':
                sri.display_name = sri.description_name
            else:
                sri.display_name = sri.name

    def name_get(self):
        result = []
        if self.env.context.get('grn_fot_allocation') or (self.env.context.get('code') and self.env.context.get('code') == 5):
            print(self.env.context)
            for rec in self:
                if rec.picking_type_id.operation == 'station':
                    result.append((rec.id, rec.description_name))
                else:
                    result.append((rec.id, rec.name))
        else:
            for rec in self:
                result.append((rec.id, rec.name))
        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        check = []
        args += ['|', ('name', operator, name), ('description_name', operator, name)]
        backorder = self.search(args + domain, limit=limit)
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
                check += [('warehouse_id.code', 'in', ['FA', 'KTN-LT-N', 'KTN-AP-N']),
                           ('partner_id', '=', self._context.get('partner_id')),
                           ('state', 'not in', ['done', 'cancel', 'draft']), ('picking_type_id.operation', '=', 'factory'),
                           ('picking_type_id.code', '=', 'incoming'),
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
                args += [('warehouse_id.code', 'in', ['FA', 'KTN-LT-N', 'KTN-AP-N']),
                           ('partner_id', '=', self._context.get('partner_id')),
                            ('picking_type_id.operation', '=', 'factory'),
                            ('date_done', '>=', self._context.get('date')),
                           ('picking_type_id.code', '=', 'incoming'), ('id', 'not in', grn_array),
                            ('id', 'not in', arr_done), ('product_id', '=', self._context.get('product_id')),
                         ('state', 'not in', ['done', 'cancel', 'draft']), ('backorder_id', '=', False)]
                backorder = self.search(args + domain, limit=limit)

            if self._context.get('payment_percent') == 100:
                if self.env.context.get('factory'):
                    check += [('warehouse_id.code', 'in', ['FA', 'KTN-LT-N', 'KTN-AP-N']),
                              ('partner_id', '=', self._context.get('partner_id')),
                              ('state', 'in', ['done']),
                              ('date_done', '>=', self._context.get('date')),
                              ('picking_type_id.operation', '=', 'factory'),
                              ('picking_type_id.code', '=', 'incoming'),
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
                    args += [('warehouse_id.code', 'in', ['FA', 'KTN-LT-N', 'KTN-AP-N']),
                             ('partner_id', '=', self._context.get('partner_id')),
                             ('picking_type_id.operation', '=', 'factory'),
                             ('date_done', '>=', self._context.get('date')),
                             ('picking_type_id.code', '=', 'incoming'), ('id', 'not in', grn_array),
                             ('id', 'not in', arr_done), ('product_id', '=', self._context.get('product_id')),
                             ('state', 'in', ['done']), ('backorder_id', '=', False)]
                    backorder = self.search(args + domain, limit=limit)
                else:
                    check += [('warehouse_id.code', 'in', ['FA', 'KTN-LT-N', 'KTN-AP-N']),
                              ('partner_id', '=', self._context.get('partner_id')),
                              ('state', 'in', ['done']),
                              ('date_done', '>=', self._context.get('date')),
                              ('picking_type_id.operation', '=', 'station'),
                              ('picking_type_id.code', '=', 'incoming'),
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
                             ('picking_type_id.operation', '=', 'station'),
                             ('date_done', '>=', self._context.get('date')),
                             ('picking_type_id.code', '=', 'incoming'), ('id', 'not in', grn_array),
                             ('id', 'not in', arr_done), ('product_id', '=', self._context.get('product_id')),
                             ('state', 'in', ['done']), ('backorder_id', '=', False)]
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
                check += [('warehouse_id.code', 'in', ['FA', 'KTN-LT-N', 'KTN-AP-N']),
                          ('partner_id', '=', self._context.get('partner_id')),
                        ('picking_type_id.operation', '=', 'factory'),
                          ('date_done', '>=', self._context.get('date')),
                          ('picking_type_id.code', '=', 'incoming'),
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
                domain += [('warehouse_id.code', 'in', ['FA', 'KTN-LT-N', 'KTN-AP-N']),
                         ('partner_id', '=', self._context.get('partner_id')),
                         ('picking_type_id.operation', '=', 'factory'),
                           ('date_done', '>=', self._context.get('date')),
                         ('picking_type_id.code', '=', 'incoming'), ('id', 'not in', grn_array),
                         ('id', 'not in', arr_done), ('product_id', '=', self._context.get('product_id')),
                         ('state', 'not in', ['done', 'cancel', 'draft']), ('backorder_id', '=', False)]
            if self._context.get('payment_percent') == 100:
                if self.env.context.get('factory'):
                    check += [('warehouse_id.code', 'in', ['FA', 'KTN-LT-N', 'KTN-AP-N']),
                              ('partner_id', '=', self._context.get('partner_id')),
                              ('picking_type_id.operation', '=', 'factory'),
                              ('date_done', '>=', self._context.get('date')),
                              ('picking_type_id.code', '=', 'incoming'),
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
                    domain += [('warehouse_id.code', 'in', ['FA', 'KTN-LT-N', 'KTN-AP-N']),
                               ('partner_id', '=', self._context.get('partner_id')),
                               ('picking_type_id.operation', '=', 'factory'),
                               ('date_done', '>=', self._context.get('date')),
                               ('picking_type_id.code', '=', 'incoming'), ('id', 'not in', grn_array),
                               ('id', 'not in', arr_done), ('product_id', '=', self._context.get('product_id')),
                               ('state', 'in', ['done']), ('backorder_id', '=', False)]
                else:
                    check += [('warehouse_id.code', 'in', ['FA', 'KTN-LT-N', 'KTN-AP-N']),
                              ('partner_id', '=', self._context.get('partner_id')),
                              ('picking_type_id.operation', '=', 'station'),
                              ('date_done', '>=', self._context.get('date')),
                              ('picking_type_id.code', '=', 'incoming'),
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
                               ('picking_type_id.operation', '=', 'station'),
                               ('date_done', '>=', self._context.get('date')),
                               ('picking_type_id.code', '=', 'incoming'), ('id', 'not in', grn_array),
                               ('id', 'not in', arr_done), ('product_id', '=', self._context.get('product_id')),
                               ('state', 'in', ['done']), ('backorder_id', '=', False)]
        return super(StockPicking, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit,
                                                     order=order)
