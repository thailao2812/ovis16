# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
# from account_payment import (
#     URL_CONFIG, TOKEN_CONFIG,
#     pre_synchronize_value, request_api, pre_create_sync_value
# )
import ast

import requests
import json
from datetime import datetime

DATE_FORMAT = "%Y-%m-%d"


def format_date_format(date_value):
    _date = datetime.strptime(date_value, '%d/%m/%Y')
    return datetime.strftime(_date, DATE_FORMAT)

def pre_synchronize_value(payload, response):
    value = {
        'slc_method': 'patch',
        'payload': json.dumps(payload),
        'result': response.status_code in [200] and 'done' or response.text,
        'state': response.status_code in [200] and 'done' or 'failed',
    }
    return {
        'result': response.status_code in [200] and 'done' or response.text,
        'state': response.status_code in [200] and 'done' or 'failed',
        'is_run': False,
        'line_ids': [(0, 0, value)]
    }


def pre_create_sync_value(model, payload, response):
    synchronize_value = json.loads(str(response.text))
    value = {
        'slc_method': 'post',
        'payload': json.dumps(payload),
        'result': 'done',
        'state': 'done',
    }
    if synchronize_value['data']:
        return {
            'res_id_syn': synchronize_value['result']['data']['data'][0]['id'],
            'model_syn': model,
            'name_syn': synchronize_value['result']['data']['data'][0]['display_name'],
            'slc_method': 'post',
            'result': 'Create Done',
            'state': 'done',
            'line_ids': [(0, 0, value)]
        }
    else:
        return {
            # 'res_id_syn': synchronize_value['data'][0]['id'],
            'model_syn': model,
            # 'name_syn': synchronize_value['data'][0]['name'],
            'slc_method': 'post',
            'result': 'Create Done',
            'state': 'failed',
            # 'line_ids': [(0, 0, value)]
        }


def request_api(method, url, payload, headers):
    return requests.request(method, url, data=payload, headers=headers)

class AccountMove(models.Model):
    _inherit = 'account.move'

    def button_cancel(self):
        res = super(AccountMove, self).button_cancel()
        for rcs in self:
            if rcs.state == 'draft':
                syn_id = self.env['api.synchronize.data'].search([
                    ('type', '=', 'transaction'),
                    ('state', '=', 'done'),
                    ('model', '=', self._name),
                    ('res_id', '=', self.id),
                    ('res_id_syn', '!=', 0),
                ], limit=1)
                if syn_id:
                    syn_id.write({
                        'is_delete': True,
                        'state': 'waiting',
                        'slc_method': 'delete',
                    })
        return res

    # def _get_default_header_request(self):
    #     url = self.env.ref(URL_CONFIG, False)
    #     access_token = self.env.ref(TOKEN_CONFIG, False)
    #     if not (url and access_token):
    #         return '', {}
    #     url = url.value + '/' + self._name
    #     return url, {
    #         'content-type': 'application/x-www-form-urlencoded',
    #         'access-token': access_token and access_token.value or False,
    #     }

    def action_api_delete(self, synchronize_id):
        url = self.env.ref(
            'api_restful.default_api_restfull_url_config',
            False)
        if url:
            url = url.value + '/' + self._name
        # get url access_token
        access_token = self.env.ref(
            'api_restful.default_api_restfull_access_token_config',
            False)

        headers = {
            'content-type': 'application/x-www-form-urlencoded',
            'access-token': access_token and access_token.value or False,
        }
        # call api action done của stock.picking
        payload = {}
        url += '/' + str(
            synchronize_id.res_id_syn) + '/' + 'action_api_delete'
        response = requests.request(
            "PATCH",
            url,
            data=payload,
            headers=headers
        )
        if response.status_code not in [200]:
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
            synchronize_id.unlink()

    @api.model
    def cron_api_move(self, date_from, date_to, limit=100):
        move_obj = self.env['account.move'].sudo()
        move_ids = move_obj.browse()
        fail_sync_ids = self.env['api.synchronize.data'].search(
            [('type', '=', 'transaction'),
             ('state', '!=', 'done'),
             ('model', '=', self._name)], limit=limit)
        if fail_sync_ids:
            move_ids |= move_obj.browse(fail_sync_ids.mapped('res_id'))
            limit = limit - len(move_ids)

        if limit > 0:
            #  Run Except Payment Invoice
            #  mục đích để loại bỏ các bút toán payment
            # self.get_payment_move(format_date_format(date_from),
            #                       format_date_format(date_to))
            domain = [
                # ('asset_id', '=', False),
                      ('journal_id.is_api', '=', True),
                      ('move_type', '=', 'entry'),
                      ('journal_id.type', '=', 'purchase'),
                      ('id', 'not in', self._get_synchronized_ids())]
            if date_to:
                domain += [('date', '<=', format_date_format(date_to))]
            if date_from:
                domain += [('date', '>=', format_date_format(date_from))]
            move_ids |= move_obj.search(domain, limit=limit)

        sync_ids = fail_sync_ids.filtered(lambda x:
            x.is_delete and x.res_id_syn)

        # loại bỏ các account move delete
        if sync_ids:
            for sys in sync_ids:
                move_ids -= sys.mapped('reference')
                self.action_api_delete(sys)

        for move in move_ids:
            synchronize_id = fail_sync_ids.filtered(
                lambda x: x.res_id == move.id and x.model == self._name)
            move.action_api_create(synchronize_id)
        return True

    def action_api_create(self,synchronize_id):
        for rcs in self:
            url = self.env.ref(
                'api_restful.default_api_restfull_url_config',
                False)
            if url:
                url = url.value + '/' + 'account.move'
            # get url access_token
            access_token = self.env.ref(
                'api_restful.default_api_restfull_access_token_config',
                False)
            headers = {
                'content-type': 'application/json',
                'access-token': access_token and access_token.value or False,
            }
            model = self._name
            if not synchronize_id:
                synchronize_id = self.env['api.synchronize.data'].create({
                    'name': rcs.name,
                    'model': rcs._name,
                    'res_id': rcs.id,
                    'type': 'transaction',
                    'slc_method': 'post',
                })
            if not synchronize_id.res_id_syn:
                payload = rcs._prepare_value()
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
                synchronize_id.write({
                    'res_id_syn': synchronize_value['result']['data']['data'][0]['id'],
                    'model_syn': 'account.move',
                    'name_syn': synchronize_value['result']['data']['data'][0]['display_name'],
                    'slc_method': 'post',
                    'result': 'Create Done',
                    'state': 'waiting',
                    'line_ids': [(0, 0, value)]
                })
                if rcs.state == 'draft':
                    continue
                payload = {}
                payload = json.dumps(payload)
                url += '/' + str(synchronize_id.res_id_syn) + '/post'
                response = requests.request(
                    "PATCH",
                    url,
                    data=payload,
                    headers=headers
                )
                synchronize_value = json.loads(str(response.text))
                if response.status_code not in [200] or response.status_code in [200] and \
                        ('error' in synchronize_value[
                            'result'] if 'result' in synchronize_value else 'error' in synchronize_value):
                    value = {
                        'slc_method': 'patch',
                        'payload': payload,
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
                        'payload': payload,
                        'result': 'done',
                        'state': 'done',
                    }
                    synchronize_id.write({
                        'result': response.text,
                        'state': 'done',
                        'is_run': False,
                        'line_ids': [(0, 0, value)]
                    })
            return synchronize_id

    def _get_synchronized_ids(self):
        done_sync_ids = self.env['api.synchronize.data'].search(
            [('type', '=', 'transaction'),
             ('state', '=', 'done'),
             ('model', '=', self._name)])
        config = self.env.ref('api_restful.api_account_move_except_config')
        except_values = ast.literal_eval(config.value)
        return done_sync_ids.mapped('res_id') + except_values

    def get_payment_move(self, date_from, date_to):
        invoice_obj = self.env['account.invoice']
        payment_obj = self.env['account.payment']
        move_line_obj = self.env['account.move.line']
        invoices = invoice_obj.search(
            [('date_invoice', '>=', date_from),
             ('date_invoice', '<=', date_to)])
        payments = payment_obj.search(
            [('payment_date', '>=', date_from),
             ('payment_date', '<=', date_to)]
        )
        moves = []
        for inv in invoices:
            action = inv.action_view_move_line()
            if not action:
                continue
            domain = action.get('domain', False)
            move_lines = move_line_obj.search(domain)
            moves += move_lines.mapped('move_id').ids
        for payment in payments:
            action = payment.action_view_invoice_move_line()
            if not action:
                continue
            domain = action.get('domain', False)
            move_lines = move_line_obj.search(domain)
            moves += move_lines.mapped('move_id').ids
        config = self.env.ref('api_restful.api_account_move_except_config')
        config.write({'value': str(list(set(moves)))})

    def _prepare_value(self):
        value = {
            'name': self.name or '',
            'ref': self.ref or '',
            'payment_reference': self.narration or '',
            'date': str(self.date) or '',
            'journal_id': self.journal_id.sync_id,
            'currency_id': self.currency_id and self.currency_id.sync_id or False,
            'analytic_account_id': self.account_analytic_id and self.account_analytic_id.sync_id or False,
            'move_type': 'entry',
            'partner_id': self.partner_id and self.partner_id.sync_id or False,
            'invoice_date_due': str(self.date) or '',
            'invoice_date': str(self.date) or '',
            'line_ids': self._prepare_value_line_ids()
        }
        currency_rate = 0
        if self.line_ids:
            value.update({'rate_type': self.line_ids[0].rate_type})
            if self.currency_id == self.env.ref('base.VND'):
                currency_rate = self.line_ids[0].currency_ex_rate
        value.update({'currency_rate': currency_rate})
        return value

    def _prepare_value_line_ids(self):
        return [(0, 0, self._prepare_value_line(x))
                                        for x in self.line_ids]

    def _prepare_value_line(self, move_line):
        return {
            'name': move_line.name,
            'ref': move_line.ref,
            # 'group_cp': move_line.group_cp,
            'account_id': move_line.account_id.sync_id,
            # 'analytic_account_id': move_line.analytic_account_id.sync_id,
            'amount_currency': move_line.amount_currency,
            'currency_id': move_line.currency_id.sync_id,
            'debit': move_line.debit,
            'credit': move_line.credit,
            'partner_id': move_line.partner_id.sync_id,
        }

    def action_api_update(self, sync_id):
        url, headers = self._get_default_header_request()
        model = self._name
        move = self.env['account.move']
        for rcs in self:
            synchronize_id = sync_id
            if rcs == move:
                value = {
                    'slc_method': 'put',
                    'result': 'Record does not exist or has been deleted',
                    'state': 'failed',
                }
                synchronize_id.write({
                    'result': 'Record does not exist or has been deleted',
                    'state': 'failed',
                    'line_ids': [(0, 0, value)]
                })
                return synchronize_id
            if url:
                # url = url.value + '/' + synchronize_id.model_syn
                url += '/' + str(synchronize_id.res_id_syn)
            if synchronize_id.res_id_syn:
                # call api
                if not rcs.line_ids:
                    currency_rate = 0
                else:
                    currency_rate = rcs.line_ids[0].currency_ex_rate
                payload = {
                    'currency_rate': currency_rate,
                }
                response = requests.request(
                    "PUT",
                    url,
                    data=payload,
                    headers=headers
                )
                if response.status_code not in [200]:
                    value = {
                        'slc_method': 'put',
                        'payload': json.dumps(payload),
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
                    'slc_method': 'put',
                    'payload': json.dumps(payload),
                    'result': 'done',
                    'state': 'done',
                }
                synchronize_value = json.loads(str(response.text))
                synchronize_id.write({
                    'res_id_syn': synchronize_value['data'][0]['id'],
                    # 'model_syn': 'account.move',
                    'name_syn': synchronize_value['data'][0]['name'],
                    'slc_method': 'put',
                    'result': 'Update Done',
                    'state': 'done',
                    'is_run': False,
                    'line_ids': [(0, 0, value)]
                })
        return synchronize_id

    @api.model
    def cron_api_move_update(self, model, limit=100):
        move_obj = self.env['account.move'].sudo()
        move_ids = move_obj.browse()
        sync_ids = self.env['api.synchronize.data'].search([
            ('type', '=', 'transaction'),
            ('state', 'in', ['waiting']),
            ('is_run', '=', True),
            ('model', '=', self._name),
        ], limit=limit)

        # sync_ids = self.env['api.synchronize.data'].search([
        #     ('id', '=', 29703),
        # ], limit=limit)
        move_ids |= sync_ids.mapped('reference')
        for move in move_ids:
            if not move:
                continue
            move_line_ids = self.env['account.move.line'].search([
                ('move_id', '=', move.id)
            ])
            sync_id = sync_ids.filtered(lambda x:
                                        x.res_id == move.id and x.model == self._name)
            move_id = self.env['account.move'].browse(sync_id[0].res_id)
            if not move_id or not move_line_ids:
                sync_id.write({
                    'slc_method': 'put',
                    'result': '{"type": "exception", "message": "Unexpected RecordCache(account.move())"}',
                    'state': 'failed',
                })
                continue
            move.action_api_update(sync_id)
        return True
