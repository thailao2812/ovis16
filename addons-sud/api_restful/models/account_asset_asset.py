# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID

import requests
import json
from datetime import datetime
from account_payment import (
    pre_synchronize_value, request_api, pre_create_sync_value
)
import logging
_logger = logging.getLogger(__name__)

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class AccountAssetAsset(models.Model):

    _inherit = "account.asset.asset"

    def _create_asset_vals_api(self):
        asset_vals = {
            'original_value': self.value,
            'prorata_date': self.date,
            'account_analytic_id': self.account_analytic_id and \
                                   self.account_analytic_id.sync_id or False,
            # 'asset_type': self.asset_type,
            'code': self.code,
            'currency_id': self.currency_id and \
                           self.currency_id.sync_id or False,
            'method': self.method,
            'method_number': self.method_number,
            'method_period': str(self.method_period),
            'method_progress_factor': self.method_progress_factor,
            'name': self.name,
            'prorata': self.prorata,
            'salvage_value': self.salvage_value,
            'value_residual': self.value_residual,
            'is_api': 'True',
            'model_id': self.category_id and self.category_id.sync_id or False,
            'account_depreciation_expense_id': self.account_income_recognition_id \
                                             and self.account_income_recognition_id.sync_id or False,
        }
        if self.category_id.journal_id.id == 11:
            asset_vals.update({
                'asset_type': 'purchase'
            })
        else:
            asset_vals.update({
                'asset_type': 'expense'
            })

        if self.depreciation_line_ids:
            asset_vals.update({
                '__api__depreciation_move_ids': str(self._prepare_depreciation_line_api())
            })
        return asset_vals

    def _prepare_depreciation_line_api_0(self):
        ls = self._prepare_depreciation_line_api()
        ls.pop(0)
        return ls

    def _prepare_depreciation_line_api(self):
        values = [
            'account.move',
            (5, 0, 0)
        ]
        for invoice in self.depreciation_line_ids:
            values += [(0, 0, {
                'name': invoice.move_id and invoice.move_id.name or "/" ,
                'ref': invoice.move_id and invoice.move_id.name or "/" ,
                'payment_reference': invoice.name,
                'move_type': 'entry',
                # 'currency_rate': self.currency_rate,
                'date': invoice.depreciation_date or '',
                'invoice_date_due': invoice.depreciation_date or '',
                'invoice_date': invoice.depreciation_date or '',
                'auto_post': False,
                'amount_total': invoice.amount,
                'asset_value': invoice.value,
                'asset_depreciation_value': invoice.amount,
                'asset_depreciated_value': invoice.depreciated_value,
                'asset_remaining_value': invoice.remaining_value,
                'asset_value_change': False,
                'analytic_account_id': invoice.account_analytic_id and \
                                       invoice.account_analytic_id.sync_id or False,
                'currency_id': self.currency_id and self.currency_id.sync_id or False,
                'journal_id': self.category_id.journal_id and self.category_id.journal_id.sync_id or False,
                'move_check': invoice.move_check,
                'rate_type': invoice.move_id and invoice.move_id.line_ids[0].rate_type or ''
            })]
        return values

    def action_api_create(self, synchronize_id):
        for rcs in self:
            url = self.env.ref(
                'api_restful.default_api_restfull_url_config',
                False)
            if url:
                url = url.value + '/' + 'account.asset'
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
                payload = rcs._create_asset_vals_api()
                if rcs.invoice_id:
                    rcs._api_update_asset(url, headers, payload)
                    continue

                response = requests.request(
                    "POST",
                    url,
                    data=payload,
                    headers=headers
                )
                if response.status_code not in [200]:
                    value = {
                        'slc_method': 'post',
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
                    'slc_method': 'post',
                    'payload': json.dumps(payload),
                    'result': 'done',
                    'state': 'done',
                }
                synchronize_value = json.loads(str(response.text))
                if synchronize_value['data']:
                    synchronize_id.write({
                        'res_id_syn': synchronize_value['data'][0]['id'],
                        'model_syn': rcs._name,
                        'name_syn': synchronize_value['data'][0]['name'],
                        'slc_method': 'post',
                        'result': 'Create Done',
                        'state': 'waiting',
                        'line_ids': [(0, 0, value)]
                    })
                else:
                    synchronize_id.write({
                        # 'res_id_syn': synchronize_value['data'][0]['id'],
                        'model_syn': rcs._name,
                        # 'name_syn': synchronize_value['data'][0]['name'],
                        'slc_method': 'post',
                        'result': 'Create Done',
                        'state': 'failed',
                        # 'line_ids': [(0, 0, value)]
                    })
            return synchronize_id

    def _api_update_asset(self, url, headers, payload):
        sync_invoice_id = self.invoice_id.create_invoice_purchase()
        purchase_invoice_id = sync_invoice_id.res_id_syn or False
        _url = url.replace('account.asset', 'account.move')
        _url = _url + '/%s/%s' % (
            str(purchase_invoice_id), '_update_asset_info')
        payload.update({
            'depreciation_move_ids': self._prepare_depreciation_line_api_0(),
            'is_api': True,
        })
        if '__api__depreciation_move_ids' in payload:
            del payload['__api__depreciation_move_ids']
        del payload['__api_boolean__is_api']
        args = {'args': str([payload])}
        response = request_api("PATCH", _url, args, headers)
        synchronize_id = self.env['api.synchronize.data'].search(
            [('res_id', '=', self.id), ('model', '=', self._name)])
        if not synchronize_id:
            synchronize_id = self.env['api.synchronize.data'].create({
                'name': self.name,
                'model': self._name,
                'res_id': self.id,
                'type': 'transaction',
                'slc_method': 'post',
            })
        _logger.warning(response.text)
        if response.status_code not in [200]:
            synchronize_id.write(pre_synchronize_value(payload, response))
            return
        pre_sync_value = pre_create_sync_value('account.move', payload, response)
        synchronize_id.write(pre_sync_value)
        _url = url + '/' + str(synchronize_id.res_id_syn) + '/' + 'api_button_done'
        response = request_api("PATCH", _url, {}, headers)
        pre_sync_value_patch = pre_synchronize_value({}, response)
        if pre_sync_value_patch.get('line_ids', False):
            pre_sync_value_patch['line_ids'] = pre_sync_value.get(
                'line_ids', []) + pre_sync_value_patch['line_ids']
        pre_sync_value.update(pre_sync_value_patch)
        synchronize_id.write(pre_sync_value)

    @api.model
    def cron_api_account_asset(self, type, limit):
        if not limit:
            limit = 100
        asset_ids = self.env['account.asset.asset']
        list_pay_ids = []
        synchronize_pay_ids = self.env['api.synchronize.data'].search([
            ('type', '=', 'transaction'),
            ('state', '!=', 'done'),
            ('model', '=', self._name),
        ], limit=limit)
        # lọc ra các phiếu kho đã đồng bộ thành công
        synchronize_done_ids = self.env['api.synchronize.data'].search([
            ('type', '=', 'transaction'),
            ('state', '=', 'done'),
            ('model', '=', self._name),
        ])
        if synchronize_pay_ids:
            asset_ids |= synchronize_pay_ids.mapped('reference')
            limit = limit - len(asset_ids)
        if limit > 0:
            domain = []
            # Loc phiếu đã done
            if synchronize_done_ids:
                list_pay_ids += synchronize_done_ids.mapped('reference').ids
            # Lọc phiếu pay faild
            if asset_ids:
                list_pay_ids += asset_ids.ids
            if list_pay_ids:
                domain += [('id', 'not in', list_pay_ids)]

            # domain = [('id', 'in', [199])]
            asset_ids |= self.env[self._name].search(domain, limit=limit)
        for asset in asset_ids:
            synchronize_id = synchronize_pay_ids.filtered(
                lambda x: x.res_id == asset.id and x.model == self._name)
            asset.action_api_script(synchronize_id)
        return True

    def action_api_restful_token(self, synchronize_id):
        for rcs in self:
            url = self.env.ref(
                'api_restful.default_api_restfull_url_config',
                False)
            if url:
                url = url.value + '/' + 'account.asset'
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
            url += '/' + str(synchronize_id.res_id_syn) + '/' + 'api_button_done'
            response = requests.request(
                "PATCH",
                url,
                data=payload,
                headers=headers
            )
            if response.status_code not in [200]:
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

    def action_api_script(self, synchronize_id):
        for asset in self:
            synchronize_syn_id = asset.action_api_create(synchronize_id)
            if synchronize_syn_id and synchronize_syn_id.state != 'done' and \
                    synchronize_syn_id.slc_method in ['post', 'patch']:
                asset.action_api_restful_token(synchronize_syn_id)
