# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval as eval
from odoo import api, fields, models
from datetime import datetime
from pytz import timezone
import requests
import json

from odoo.models import BaseModel
import logging
_logger = logging.getLogger(__name__)

native_write_api = BaseModel.write

# def new_native_write_api(self, vals):
#     """
#     Inherit funtion write BaseModel để check xử lý cho tất cả các model
#     """
#     native = native_write_api(self, vals)
#     for rcs in self:
#         model_id = self.env['ir.model'].sudo().search([
#             ('model', '=', 'api.synchronize.data')
#         ])
#         if not model_id:
#             continue
#         model_api_id = self.env['ir.model'].sudo().search([
#             ('model', '=', rcs._name)
#         ])
#         fields = model_api_id.fields_get()
#         if model_api_id and 'restful_api' in fields:
#             if not model_api_id.restful_api:
#                 continue
#         sql = '''
#         SELECT id
#         FROM api_synchronize_data
#         WHERE model = '%(model)s'
#         AND res_id = %(res_id)s
#         AND state = 'done'
#         ''' % ({
#             'model': rcs._name,
#             'res_id': rcs.id,
#         })
#         self.env.cr.execute(sql)
#         for synchronize in self.env.cr.dictfetchall():
#             # allocation = synchronize['id']
#             synchronize_id = self.env['api.synchronize.data'].browse(synchronize['id'])
#             config_id = self.env['api.synchronize.data.config'].search([
#                 ('model', '=', self._name),
#                 ('state', '=', 'post'),
#             ], limit=1)
#             if config_id and any(
#                     field in config_id.mapped('line_ids.fields_name') \
#                     for field in vals):
#                 # create data line để đợi update
#                 self.env['api.synchronize.data.line'].create({
#                     'synchronize_id': synchronize_id.id,
#                     'slc_method': 'put',
#                     'result': 'Waiting',
#                     'state': 'waiting'
#                 })
#                 synchronize_id.write({
#                     'state': 'waiting',
#                     'result': 'Waiting',
#                 })
#     return native


@api.model
def synchronize_data_by_fields(self, new_model, domain_set, extend_action="write", doall=True):
    if extend_action == "write":
        self.synchronize_data_write(new_model, domain_set, doall)
    if extend_action == "create":
        self.synchronize_data_create(new_model, domain_set, doall)


def default_request(self, extend_url=""):
    url = self.env.ref('api_restful.default_api_restfull_url_config', False)
    if not url:
        return '', {}
    url = url.value + extend_url
    access_token = self.env.ref(
        'api_restful.default_api_restfull_access_token_config', False)
    headers = {
        'content-type': 'application/json',
        'access-token': access_token and access_token.value or False,
    }
    return url, headers


def synchronize_data_write(self, new_model, domain_set, doall=True):
    url, headers = self.default_request('/search/' + new_model)
    if not url:
        return
    sync_domain = self.get_doall_domain_model(doall)
    sync_domain += self.get_sync_domain_model(new_model)
    for r in self.with_context(active_test=False).search(sync_domain):
        values = {}
        for a, b in domain_set:
            value = getattr(r, a)
            values.update({b: value})

        payload = json.dumps(values)
        response = requests.request("GET", url, data=payload, headers=headers)
        if response.status_code in [200]:
            result = json.loads(response.text)
            if result.get('result', False):
                if isinstance(result['result'], (str)):
                    result = json.loads(result['result'])
                else:
                    result = result['result']
                if result.get('error', False):
                    _logger.warning(result['error'])
                if result.get('data', False):
                    r.write({'sync_id': result['data'][0]})
        else:
            _logger.warning(response.text)


def synchronize_data_create(self, new_model, domain_set, doall=True):
    url, headers = self.default_request('/' + new_model)
    if not url:
        return
    sync_domain = self.get_doall_domain_model(doall)
    sync_domain += self.get_sync_domain_model(new_model)
    for r in self.with_context(active_test=False).search(sync_domain, limit=1):
        values = {'sync_id': r.id}
        for a, b in domain_set:
            value = getattr(r, a)

            if 'sync_id' in dir(value):
                value = value.sync_id
            values.update({b: value})

        payload = json.dumps(values)
        response = requests.request("POST", url, data=payload, headers=headers)
        if response.status_code in [200]:
            result = json.loads(response.text)
            if result.get('error', False):
                _logger.warning(result['error'])
                continue
            if result.get('result', False):
                if isinstance(result['result'], (str)):
                    result = json.loads(result['result'])
                else:
                    result = result['result']
                if result.get('error', False):
                    _logger.warning(result['error'])
                    continue
                if result.get('data', False):
                    r.write({'sync_id': result['data']['data'][0]['id']})
        else:
            _logger.warning(response.text)


def get_sync_domain_model(self, new_model):
    domain_config = self.env['api.synchronize.domain.config'].search(
        [('new_model', '=', new_model)])
    if not domain_config:
        return []
    return expression.normalize_domain(eval(domain_config.domain))


def get_doall_domain_model(self, doall):
    if 'sync_id' in dir(self) and not doall:
        return [('sync_id', '=', 0)]
    return []



@api.model
def action_api_sync_parent_id(self, parent_field, new_parent_field, new_model=''):
    access_token = self.env.ref(
        'api_restful.default_api_restfull_access_token_config',
        False)
    url = self.env.ref(
        'api_restful.default_api_restfull_url_config', False)
    if not (url and access_token):
        return
    headers = {
        'content-type': 'application/json',
        'access-token': access_token and access_token.value or False,
    }
    records = self.env['api.synchronize.data'].search(
        [('model', '=', self._name)])
    record_ids = []
    if records:
        res_ids = records.mapped('res_id')
        record_ids = self.browse(res_ids).filtered(
            lambda r: getattr(r, parent_field))
    else:
        record_ids = self.with_context(active_test=False).search(
            [(parent_field, '!=', False)])
    for rec in record_ids:
        parent_obj = getattr(rec, parent_field)
        if 'sync_id' in dir(parent_obj) and rec.sync_id and parent_obj.sync_id:
            request_url = url.value + '/%s/%s/write' % (
                str(new_model), str(rec.sync_id))
            args = json.dumps({
                new_parent_field: parent_obj.sync_id
            })
            response = requests.request("PATCH", request_url, data=args,
                                        headers=headers)
            if response.status_code not in [200]:
                _logger.error(response.text)
            continue

        parent_sync_id = self.env['api.synchronize.data'].search(
            [('model', '=', self._name),
             ('res_id', '=', rec.parent_id.id)])
        sync_id = self.env['api.synchronize.data'].search(
            [('model', '=', self._name),
             ('res_id', '=', rec.id)])
        if not (sync_id and parent_sync_id):
            continue
        if not (sync_id.res_id_syn and parent_sync_id.res_id_syn):
            continue
        request_url = url.value + '/%s/%s/write' % (
            str(sync_id.model_syn), str(sync_id.res_id_syn))
        args = json.dumps({
            new_parent_field: parent_sync_id.res_id_syn
        })
        response = requests.request("PATCH", request_url, data=args,
                                    headers=headers)
        if response.status_code not in [200]:
            _logger.error(response.text)


BaseModel.synchronize_data_by_fields = synchronize_data_by_fields
BaseModel.synchronize_data_create = synchronize_data_create
BaseModel.synchronize_data_write = synchronize_data_write
BaseModel.default_request = default_request
BaseModel.get_sync_domain_model = get_sync_domain_model
BaseModel.action_api_sync_parent_id = action_api_sync_parent_id
# BaseModel.write = new_native_write_api
BaseModel.get_doall_domain_model = get_doall_domain_model
