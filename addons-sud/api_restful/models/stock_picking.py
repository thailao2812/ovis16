from odoo import api, fields, models, _
import requests
import json
from datetime import datetime
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

date_format = "%Y-%m-%d %H:%M:%S.%f"


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def action_api_restful_token(self, synchronize_id):
        for rcs in self:
            url = self.env.ref(
                'api_restful.default_api_restfull_url_config',
                False)
            if url:
                url = url.value + '/' + 'stock.picking'
            # get url access_token
            access_token = self.env.ref(
                'api_restful.default_api_restfull_access_token_config',
                False)

            headers = {
                'content-type': 'application/json',
                'access-token': access_token and access_token.value or False,
            }
            # call api action done của stock.picking
            payload = {}
            # url += '/' + str(synchronize_id.res_id_syn) + '/' + '_action_done'
            url += '/' + str(synchronize_id.res_id_syn) + '/' + '_api_action_done_picking_in'
            response = requests.request(
                "PATCH",
                url,
                data=json.dumps(payload),
                headers=headers
            )
            synchronize_value = json.loads(str(response.text))
            if response.status_code not in [200] or response.status_code in [200] and\
                    ('error' in synchronize_value['result'] if 'result' in synchronize_value else 'error' in synchronize_value):
                value = {
                    'slc_method': 'patch',
                    'payload': json.dumps(payload),
                    'result': response.text,
                    'state': 'failed',
                }
                synchronize_id.write({
                    'result': response.text,
                    'state': 'failed',
                    'line_ids': [(0, 0, value)]
                })
            else:
                value = {
                    'slc_method': 'patch',
                    'payload': json.dumps(payload),
                    'result': 'done',
                    'state': 'done',
                }
                synchronize_id.write({
                    'result': response.text,
                    'state': 'done',
                    'is_run': False,
                    'line_ids': [(0, 0, value)]
                })

    def _prepare_picking_line_api(self):
        values = []
        for move in self.move_line_ids_without_package:
            # product_id = self.env['api.synchronize.data'].search([
            #     ('model', '=', 'product.template'),
            #     ('res_id', '=', move.product_id.product_tmpl_id.id),
            # ])
            values.append((0, 0, {
                'product_id': move.product_id.product_tmpl_id.sync_id,
                'currency_id': move.currency_id and move.currency_id.sync_id != 0 \
                               and move.currency_id.sync_id or False,
                'price_currency': move.price_currency,
                'price_unit': move.price_unit,
                'lot_id': False,
                # 'product_uom_qty': 0,  # bypass reservation here
                'qty_done': move.qty_done,
                'product_uom_id': move.product_uom_id.sync_id,

                'location_id': move.location_id and move.location_id.sync_id != 0 \
                               and move.location_id.sync_id or False,
                'location_dest_id': move.location_dest_id and move.location_dest_id.sync_id != 0 \
                               and move.location_dest_id.sync_id or False,
            }))
        return values

    def _prepare_picking_move_line_api(self):
        values = []
        for move in self.move_line_ids_without_package:
            # product_id = self.env['api.synchronize.data'].search([
            #     ('model', '=', 'product.template'),
            #     ('res_id', '=', move.product_id.product_tmpl_id.id),
            # ])
            values += [(0, 0, {
                'product_id': move.product_id.product_tmpl_id.sync_id,
                # 'currency_id': move.currency_id and move.currency_id.sync_id != 0 \
                #                and move.currency_id.sync_id or False,
                # 'price_currency': move.price_currency,
                # 'lot_id': False,
                # 'product_uom_qty': 0,  # bypass reservation here
                'name': self.name,
                'price_unit': move.price_unit,
                'product_uom_qty': move.qty_done,
                'product_uom': move.product_uom_id.sync_id,
                'location_id': move.location_id and move.location_id.sync_id != 0 \
                               and move.location_id.sync_id or False,
                'location_dest_id': move.location_dest_id and move.location_dest_id.sync_id != 0 \
                                    and move.location_dest_id.sync_id or False,
            })]
        return values

    def action_api_create(self, synchronize_id, pick_type):
        for rcs in self:
            url = self.env.ref(
                'api_restful.default_api_restfull_url_config',
                False)
            if url:
                url = url.value + '/' + 'stock.picking'
            # get url access_token
            access_token = self.env.ref(
                'api_restful.default_api_restfull_access_token_config',
                False)
            headers = {
                'content-type': 'application/json',
                'access-token': access_token and access_token.value or False,
            }
            if not synchronize_id:
                synchronize_id = self.env['api.synchronize.data'].create({
                    'name': rcs.name,
                    'model': rcs._name,
                    'res_id': rcs.id,
                    'type': 'transaction',
                    'slc_method': 'post',
                })

            if not synchronize_id.res_id_syn:
                # call api
                partner_id = self.env['api.synchronize.data'].search([
                    ('model', '=', 'res.partner'),
                    ('res_id', '=', rcs.partner_id.id),
                ])
                if rcs.rate_ptbf > 0:
                    payload = {
                        'name': rcs.name,
                        'picking_type_id': rcs.picking_type_id and \
                                           rcs.picking_type_id.sync_id or False,
                        # 'partner_id': partner_id and partner_id.res_id_syn or False,
                        'partner_id': rcs.partner_id and rcs.partner_id.sync_id or False,
                        'date': str(rcs.date_done.strftime(DATETIME_FORMAT)),
                        'date_done': str(rcs.date_done.strftime(DATETIME_FORMAT)),
                        'origin': rcs.origin,
                        'location_id': rcs.location_id and rcs.location_id.sync_id != 0 \
                                       and rcs.location_id.sync_id or False,
                        'location_dest_id': rcs.location_dest_id and rcs.location_dest_id.sync_id != 0 \
                                            and rcs.location_dest_id.sync_id or False,
                        'rate_ptbf': rcs.rate_ptbf
                        # 'company_id': self.company_id.id,
                    }
                else:
                    payload = {
                        'name': rcs.name,
                        'picking_type_id': rcs.picking_type_id and \
                                           rcs.picking_type_id.sync_id or False,
                        # 'partner_id': partner_id and partner_id.res_id_syn or False,
                        'partner_id': rcs.partner_id and rcs.partner_id.sync_id or False,
                        'date': str(rcs.date_done.strftime(DATETIME_FORMAT)),
                        'date_done': str(rcs.date_done.strftime(DATETIME_FORMAT)),
                        'origin': rcs.origin,
                        'location_id': rcs.location_id and rcs.location_id.sync_id != 0 \
                                       and rcs.location_id.sync_id or False,
                        'location_dest_id': rcs.location_dest_id and rcs.location_dest_id.sync_id != 0 \
                                            and rcs.location_dest_id.sync_id or False,
                        # 'company_id': self.company_id.id,
                    }
                if pick_type == 'in':
                    payload.update({
                        'move_line_ids_without_package': rcs._prepare_picking_line_api()
                    })
                else:
                    payload.update({
                        'move_ids_without_package': rcs._prepare_picking_move_line_api()
                    })
                payload = json.dumps(payload)
                response = requests.request(
                    "POST",
                    url,
                    data=payload,
                    headers=headers
                )
                synchronize_value = json.loads(str(response.text))
                if response.status_code not in [200] or response.status_code in [200] and \
                        ('error' in synchronize_value[
                            'result'] if 'result' in synchronize_value else 'error' in synchronize_value):
                    value = {
                        'slc_method': 'post',
                        'payload': payload,
                        'result': response.text,
                        'state': 'failed',
                    }
                    synchronize_id.write({
                        'result': response.text,
                        'state': 'failed',
                        'line_ids': [(0, 0, value)]
                    })
                    continue
                value = {
                    'slc_method': 'post',
                    'payload': payload,
                    'result': 'done',
                    'state': 'done',
                }

                if pick_type == 'in':
                    state = 'waiting'
                else:
                    state = 'done'
                synchronize_id.write({
                    'res_id_syn': synchronize_value['result']['data']['data'][0]['id'],
                    'model_syn': rcs._name,
                    'name_syn': synchronize_value['result']['data']['data'][0]['display_name'],
                    'slc_method': 'post',
                    'result': 'Create Done',
                    'state': state,
                    'line_ids': [(0, 0, value)]
                })
            return synchronize_id

    @api.model
    def cron_api_picking_in(self, from_date, to_date, limit):
        if not limit:
            limit = 100
        picking_ids = self.env['stock.picking']
        list_picking_ids = []
        # chay lại cac transaction lỗi
        synchronize_pick_ids = self.env['api.synchronize.data'].search([
            ('type', '=', 'transaction'),
            ('state', '!=', 'done'),
            ('model', '=', self._name),
            '|', ('is_delete', '=', False), ('is_run', '=', False),
        ], limit=limit)
        # lọc ra các phiếu kho đã đồng bộ thành công
        synchronize_pick_done_ids = self.env['api.synchronize.data'].search([
            ('type', '=', 'transaction'),
            ('state', '=', 'done'),
            ('model', '=', self._name),
        ])

        if synchronize_pick_ids:
            picking_ids = picking_ids.browse(synchronize_pick_ids.mapped('res_id'))
            limit = limit - len(picking_ids)

        if limit > 0:
            from_date = datetime.strptime(from_date, '%d/%m/%Y')
            from_date = datetime.strftime(from_date, DATE_FORMAT)
            domain = [
                ('picking_type_id.is_api', '=', True),
                ('date_done', '>=', from_date),
                ('state', '=', 'done'),
                ('picking_type_id.code', '=', 'incoming'),
            ]
            if to_date:
                to_date = datetime.strptime(to_date, '%d/%m/%Y')
                to_date = datetime.strftime(to_date, DATE_FORMAT)
                domain += [('date_done', '<=', to_date)]
            if synchronize_pick_done_ids:
                list_picking_ids += synchronize_pick_done_ids.mapped('res_id')
            if picking_ids:
                list_picking_ids += picking_ids.ids
            if list_picking_ids:
                domain += [('id', 'not in', list_picking_ids)]
            picking_ids |= self.env['stock.picking'].search(domain, limit=limit)
        for picking in picking_ids:
            synchronize_id = synchronize_pick_ids.filtered(
                lambda x: x.res_id == picking.id and x.model == self._name)
            picking.action_api_script_in(synchronize_id)
        return True

    def action_api_script_in(self, synchronize_id):
        for picking in self:
            if synchronize_id.is_delete and synchronize_id.res_id_syn:
                picking.action_api_delete_picking(synchronize_id)
                if synchronize_id.is_run and not synchronize_id.is_delete:
                    synchronize_syn_id = picking.action_api_create(
                        synchronize_id, 'in')
                    if synchronize_syn_id and synchronize_syn_id.state != 'done' and \
                            synchronize_syn_id.slc_method in ['post', 'patch']:
                        picking.action_api_restful_token(synchronize_syn_id)
            elif synchronize_id.is_run:
                synchronize_syn_id = picking.action_api_create(
                    synchronize_id, 'in')
                if synchronize_syn_id and synchronize_syn_id.state != 'done' and \
                        synchronize_syn_id.slc_method in ['post', 'patch']:
                    picking.action_api_restful_token(synchronize_syn_id)
            else:
                synchronize_syn_id = picking.action_api_create(synchronize_id, 'in')
                if synchronize_syn_id and synchronize_syn_id.state != 'done' and \
                        synchronize_syn_id.slc_method in ['post', 'patch']:
                    picking.action_api_restful_token(synchronize_syn_id)

    def action_api_script_out(self, synchronize_id):
        for picking in self:
            if synchronize_id.is_delete and synchronize_id.res_id_syn:
                picking.action_api_delete_picking(synchronize_id)
                if synchronize_id.is_run and not synchronize_id.is_delete:
                    synchronize_syn_id = picking.action_api_create(
                        synchronize_id, 'out')
            elif synchronize_id.is_run:
                synchronize_syn_id = picking.action_api_create(
                    synchronize_id, 'out')
            else:
                synchronize_syn_id = picking.action_api_create(synchronize_id,
                                                               'out')

    @api.model
    def cron_api_picking_out(self, from_date, to_date, limit):
        if not limit:
            limit = 100
        picking_ids = self.env['stock.picking']
        list_picking_ids = []
        # chay lại cac transaction lỗi
        synchronize_pick_ids = self.env['api.synchronize.data'].search([
            ('type', '=', 'transaction'),
            ('state', '!=', 'done'),
            ('model', '=', self._name),
            '|', ('is_delete', '=', False), ('is_run', '=', False),
        ], limit=limit)
        # lọc ra các phiếu kho đã đồng bộ thành công
        synchronize_pick_done_ids = self.env['api.synchronize.data'].search([
            ('type', '=', 'transaction'),
            ('state', '=', 'done'),
            ('model', '=', self._name),
        ])

        if synchronize_pick_ids:
            picking_ids |= synchronize_pick_ids.browse(synchronize_pick_ids.mapped('res_id'))
            limit = limit - len(picking_ids)

        if limit > 0:
            from_date = datetime.strptime(from_date, '%d/%m/%Y')
            from_date = datetime.strftime(from_date, DATE_FORMAT)
            domain = [
                ('picking_type_id.is_api', '=', True),
                ('date_done', '>=', from_date),
                ('state', '=', 'done'),
                ('picking_type_id.code', '=', 'outgoing')
            ]
            if to_date:
                to_date = datetime.strptime(to_date, '%d/%m/%Y')
                to_date = datetime.strftime(to_date, DATE_FORMAT)
                domain += [('date_done', '<=', to_date)]
            if synchronize_pick_done_ids:
                list_picking_ids += synchronize_pick_done_ids.mapped('res_id')
            if picking_ids:
                list_picking_ids += picking_ids.ids
            if list_picking_ids:
                domain += [('id', 'not in', list_picking_ids)]
            picking_ids |= self.env['stock.picking'].search(domain, limit=limit)
        for picking in picking_ids:
            synchronize_id = synchronize_pick_ids.filtered(
                lambda x: x.res_id == picking.id and x.model == self._name)
            picking.action_api_script_out(synchronize_id)
        return True

    def action_api_delete_picking(self, synchronize_id):
        for rcs in self:
            url = self.env.ref(
                'api_restful.default_api_restfull_url_config',
                False)
            if url:
                url = url.value + '/' + 'stock.picking'
            # get url access_token
            access_token = self.env.ref(
                'api_restful.default_api_restfull_access_token_config',
                False)

            headers = {
                'content-type': 'application/json',
                'access-token': access_token and access_token.value or False,
            }
            # call api action done của stock.picking
            payload = {}
            url += '/' + str(
                synchronize_id.res_id_syn) + '/' + '_api_action_delete_picking'
            response = requests.request(
                "PATCH",
                url,
                data=json.dumps(payload),
                headers=headers
            )
            synchronize_value = json.loads(str(response.text))
            if response.status_code not in [200] or response.status_code in [200] and\
                    ('error' in synchronize_value['result'] if 'result' in synchronize_value else 'error' in synchronize_value):
                value = {
                    'payload': json.dumps(payload),
                    'result': response.text,
                    'state': 'failed',
                    'slc_method': 'delete',
                }
                synchronize_id.write({
                    'result': response.text,
                    'state': 'failed',
                    'line_ids': [(0, 0, value)]
                })
            else:
                value = {
                    'slc_method': 'delete',
                    'payload': json.dumps(payload),
                    'result': 'done',
                    'state': 'done',
                }
                synchronize_id.write({
                    'result': response.text,
                    'state': 'done',
                    'name_syn': False,
                    'model_syn': False,
                    'res_id_syn': False,
                    'is_delete': False,
                    'line_ids': [(0, 0, value)]
                })

    def action_revert_done(self):
        for pick in self:
            res = super(StockPicking, self).action_revert_done()
            if pick.state != 'done':
                syn_invoice_done_ids = self.env['api.synchronize.data'].search([
                    ('type', '=', 'transaction'),
                    ('state', '=', 'done'),
                    ('model', '=', self._name),
                    ('res_id', '=', self.id),
                ], limit=1)
                if syn_invoice_done_ids:
                    syn_invoice_done_ids.write({
                        'is_delete': True,
                        'state': 'waiting',
                        'slc_method': 'delete',
                    })
        return res

    def action_done(self):
        res = super(StockPicking, self).action_done()
        for rcs in self:
            if rcs.state == 'done':
                syn_invoice_done_ids = self.env['api.synchronize.data'].search([
                    ('type', '=', 'transaction'),
                    ('slc_method', '=', 'delete'),
                    ('res_id', '=', rcs.id),
                    ('model', '=', rcs._name),
                ], limit=1)
                if syn_invoice_done_ids:
                    syn_invoice_done_ids.write({
                        'is_run': True,
                        'state': 'waiting',
                    })
        return res

    def do_transfer(self):
        res = super(StockPicking, self).do_transfer()
        for rcs in self:
            if rcs.state == 'done':
                syn_invoice_done_ids = self.env['api.synchronize.data'].search([
                    ('type', '=', 'transaction'),
                    ('slc_method', '=', 'delete'),
                    ('res_id', '=', rcs.id),
                    ('model', '=', rcs._name),
                ], limit=1)
                if syn_invoice_done_ids:
                    syn_invoice_done_ids.write({
                        'is_run': True,
                        'state': 'waiting',
                    })
        return res
