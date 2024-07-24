# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime
from pytz import timezone
import requests
import json

import logging
_logger = logging.getLogger(__name__)

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
NAME_DATETIME_FORMAT = "%Y%m%d.%H%M"


class SynchronizeData(models.Model):
    _name = 'api.synchronize.data'
    _description = 'API Synchronize Data'

    @api.model
    def _select_objects(self):
        models = self.env['ir.model'].search([('state', '!=', 'manual')])
        return [(model.model, model.name)
                for model in models]

    @api.depends('model', 'res_id')
    def _compute_objects(self):
        for rcs in self:
            if rcs.model and rcs.res_id:
                if rcs.model:
                    rcs.reference = '%s,%s' % (rcs.model, rcs.res_id)
                else:
                    rcs.reference = False
            else:
                rcs.reference = False

    @api.depends('line_ids', 'line_ids.slc_method')
    def _compute_slc_method(self):
        for rcs in self:
            if rcs.line_ids and rcs.line_ids[0].slc_method:
                rcs.slc_method = rcs.line_ids[0].slc_method
            else:
                rcs.slc_method = 'post'

    name = fields.Char(
        string='Name'
    )
    model = fields.Char(
        'Model Name',
    )
    res_id = fields.Integer(
        'Record ID',
        help="ID of the target record in the database"
    )

    name_syn = fields.Char(
        string='Synchronize Name'
    )
    model_syn = fields.Char(
        'Synchronize Model Name',
    )
    res_id_syn = fields.Integer(
        'Synchronize Record ID',
        help="ID of the target record in the database synchronize"
    )
    result = fields.Html(
        string='Result'
    )

    line_ids = fields.One2many(
        'api.synchronize.data.line',
        'synchronize_id',
        'synchronize line',
    )

    reference = fields.Reference(
        string='Reference record',
        compute="_compute_objects",
        selection='_select_objects',
        size=128,
    )
    state = fields.Selection(
        [
            ('draft', "Draft"),
            ('waiting', 'Waiting'),
            ('done', 'Done'),
            ('failed', 'Failed'),
        ],
        default="draft",
        string="Status",
    )
    slc_method = fields.Selection(
        [
            ('get', "Search"),
            ('post', 'Create'),
            ('put', 'Write'),
            ('patch', 'Action'),
            ('delete', 'Delete'),
        ],
        string="Method",
        compute="_compute_slc_method",
        store=True
    )

    type = fields.Selection(
        [
            ('master', "Master Data"),
            ('transaction', 'Transaction Data'),
        ],
        string="Type",
        default='master',
    )

    is_delete = fields.Boolean(
        string='Is Delete'
    )
    is_run = fields.Boolean(
        string='Is Run'
    )
    is_write = fields.Boolean(
        string='Is Write'
    )
    number_of_retries = fields.Integer(
        string='Number of Retries'
    )

    # def unlink(self):

    # for rec in self:
    #         if rec.type == 'master':
    #             raise UserError(_('You cannot delete records of this model!'))
    #     return super(SynchronizeData, self).unlink()
    #

    def prepare_payload(self, recored_id, config_id):
        if not recored_id or not config_id:
            return {}
        payload = {}
        for field in config_id.line_ids:
            fields_sys = field.fields_sys
            fields_value = recored_id. \
                read([str(field.fields_name)])[0][str(field.fields_name)]
            # Xử lý field relation many2one
            if field.ttype == 'many2one' and field.model_sys and \
                    field.value_sys:
                if not fields_value:
                    fields_value = 'False'
                else:
                    value = getattr(recored_id, str(field.fields_name))
                    if 'sync_id' in dir(value) and value.sync_id:
                        # fields_value = {'sync_value': value.sync_id or 'false'}
                        # fields_value = {field.fields_sys: value.sync_id or 'false'}
                        fields_value = value.sync_id or 'false'
                    else:
                        self.env.cr.execute('''
                                SELECT %(value_sys)s
                                FROM %(model_sys)s
                                WHERE id = %(fields_value)s
                                ''' % ({
                            'value_sys': field.value_sys,
                            'model_sys': field.relation.replace('.', '_'),
                            'fields_value': fields_value[0]
                        }))
                        field_value_sys = self.env.cr.dictfetchall()
                        fields_value = {
                            'field': field.value_sys,
                            'model_sys': field.model_sys,
                            'value': field_value_sys[0][str(field.value_sys)],
                        }
                fields_value = str(fields_value)
                # fields_sys = '__api_dict__' + field.fields_sys
            elif field.ttype == 'one2many' and field.config_sys_id:
                # Xử lý field relation one2many có giá trị
                res_ids = self.env[field.relation].browse(fields_value)
                res_value = [field.config_sys_id.model, (5, 0, 0)]
                for res_id in res_ids:
                    payload_relation = self.prepare_payload(res_id, field.config_sys_id)
                    res_value += [(0, 0, payload_relation)]
                fields_value = str(res_value)
                # fields_sys = '__api__' + field.fields_sys
            elif field.ttype == 'many2many':
                # Xử lý many2many
                res_ids = self.env[field.relation].browse(fields_value)
                fields_value_sys = res_ids and res_ids. \
                    read([str(field.value_sys)]) or False
                if fields_value_sys:
                    fields_value_sys = [
                        field.model_sys,
                        field.value_sys,
                        [key_v[field.value_sys] for key_v in fields_value_sys]
                    ]
                else:
                    fields_value_sys = False
                fields_value = str(fields_value_sys)
                # fields_sys = '__api_many2many__' + field.fields_sys
            elif field.ttype == 'boolean':
                # fields_value = {
                #     'field': field.fields_sys,
                #     'value': fields_value
                # }
                if config_id.model == 'res.partner' and config_id.new_model == 'res.partner' \
                        and (field.fields_name == 'customer' or field.fields_name == 'supplier'):
                    if not fields_value:
                        fields_value = 0
                    else:
                        fields_value = 1
                else:
                    fields_value = str(fields_value)
                # fields_sys = '__api_boolean__' + field.fields_sys
            elif field.ttype == 'date' or field.ttype == 'datetime':
                fields_value = str(fields_value)
                
            payload.update({
                fields_sys: fields_value if (
                            field.fields_name == 'customer' or field.fields_name == 'supplier') else fields_value or ''
            })
        return payload

    def run_api(self):
        for rcs in self:
            model_obj = self.env[rcs.model].with_context(active_test=False)
            recored_id = model_obj.search([('id', '=', rcs.res_id)])

            if rcs.type == 'transaction' and rcs.model == 'stock.picking':
                if recored_id.picking_type_id.code == 'incoming':
                    recored_id.action_api_script_in(rcs)
                else:
                    recored_id.action_api_script_out(rcs)
                return
            elif rcs.type == 'transaction' and rcs.model == 'account.move':
                recored_id.action_api_script_out(rcs)
                return
            elif rcs.type == 'transaction' and rcs.model == 'account.payment':
                recored_id.action_api_script_pay(rcs)
                return

            config_id = self.env['api.synchronize.data.config'].search([
                ('model', '=', rcs.model),
                ('state', '=', 'post'),
            ], limit=1)
            payload = self.prepare_payload(recored_id, config_id)
            synchronize_line_id = rcs.line_ids.sorted(key=lambda l: l.write_date)
            if rcs.slc_method == 'put'\
                    and synchronize_line_id[-1].state != 'done':
                rcs.action_write_api_synchronize(
                    payload=payload,
                    model=rcs.model
                )

            if rcs.slc_method == 'post' and \
                    synchronize_line_id[-1].state != 'done':
                rcs.action_create_api_synchronize(
                    payload=payload,
                    model=rcs.model
                )

    def action_create_api_synchronize(self, payload=False, model=False):
        url = self.env.ref(
            'api_restful.default_api_restfull_url_config', False)

        if not (payload or url):
            return
        url = url.value + '/' + model
        access_token = self.env.ref(
            'api_restful.default_api_restfull_access_token_config', False)
        headers = {
            'content-type': 'application/json',
            'access-token': access_token and access_token.value or False,
        }
        payload = json.dumps(payload)
        for synchronize_id in self:
            value = {
                'slc_method': 'post',
                'payload': payload,
            }

            # call api
            response = requests.request(
                "POST",
                url,
                data=payload,
                headers=headers,
                verify=False
            )
            result = response.text
            if response.status_code in [200] and 'error' not in result:
                synchronize_value = json.loads(str(response.text))
                synchronize_value = synchronize_value['result']['data']
                value.update({
                    'result': 'done',
                    'state': 'done',
                })
                synchronize_id.write({
                    'result': 'done',
                    'state': 'done',
                    'res_id_syn': synchronize_value['data'][0]['id'],
                    'model_syn': model,
                    'name_syn': synchronize_value['data'][0]['display_name'],
                    'line_ids': [(0, 0, value)],
                    'number_of_retries': 0
                })
                if synchronize_id.model and synchronize_id.res_id:
                    synchronize_res_id = self.env[synchronize_id.model].browse(
                        synchronize_id.res_id)
                    if 'sync_id' in dir(synchronize_res_id):
                        synchronize_res_id.write({
                            'sync_id': synchronize_value['data'][0]['id'],
                        })
            else:
                value.update({
                    'result': response.text,
                    'state': 'failed',
                })
                synchronize_id.write({
                    'result': response.text,
                    'state': 'failed',
                    'number_of_retries': synchronize_id.number_of_retries + 1,
                    'line_ids': [(0, 0, value)]
                })

    def get_retry_domain(self, model, method):
        model_name = '%\'' + model + '\'%'
        cron = self.env['ir.cron'].search([
            ('model_id.model', '=', self._name)
        ],
            # order='priority asc',
            limit=1
        )
        if cron and cron.number_of_retries:
            return cron.number_of_retries
        return 10

    @api.model
    def cron_create_api_synchronize(self, model=False, limit=False):
        if not model:
            return
        limit = limit
        if not limit:
            limit = 500

        config_id = self.env['api.synchronize.data.config'].search([
            ('model', '=', model),
            ('state', '=', 'post'),
        ], limit=1)
        if not config_id:
            return

        # check xem synchronize có nhưng chạy tạo bị Faild chạy lại
        synchronize_ids = self.env['api.synchronize.data'].search([
            ('model', '=', model),
            ('res_id', '!=', False),
            ('res_id_syn', '=', False),
            ('state', '!=', 'done'),
            ('slc_method', '=', 'post'),
            ('number_of_retries', '<', self.get_retry_domain(
                model, 'cron_create_api_synchronize'))
        ], limit=limit)
        res_ids = []
        recored_ids = self.env[model]

        if synchronize_ids:
            res_ids = synchronize_ids.mapped('res_id')
            recored_ids = self.env[model].search([
                ('id', 'in', res_ids)
            ], limit=limit)
            limit = limit - len(synchronize_ids)

        if limit > 0:
            # loại bỏ các recored_ids đã được đồng bộ thành công
            synchronize_ids = self.env['api.synchronize.data'].search([
                ('model', '=', model),
                ('res_id', '!=', False),
                ('res_id_syn', '!=', False),
                '|',
                ('slc_method', '=', 'put'),
                '&',
                ('state', '=', 'done'),
                ('slc_method', '=', 'post')
            ])
            res_ids = synchronize_ids and synchronize_ids.mapped('res_id') or []
            model_obj = self.env[model].with_context(active_test=False)
            sync_domain = [('id', 'not in', res_ids)]
            new_model = config_id.new_model
            sync_domain += self.get_sync_domain_model(new_model)
            if 'parent_id' in dir(model_obj):
                recored_ids |= model_obj.search(
                    sync_domain, limit=limit, order='parent_id desc')
            else:
                recored_ids |= model_obj.search(sync_domain, limit=limit)

        for recored in recored_ids:
            synchronize_id = self.env['api.synchronize.data'].search([
                ('model', '=', recored._name),
                ('res_id', '=', recored.id),
                ('slc_method', '=', 'post')
            ])
            if not synchronize_id:
                synchronize_id = self.env['api.synchronize.data'].create({
                    'name': recored.display_name,
                    'model': recored._name,
                    'res_id': recored.id
                })
            payload = self.prepare_payload(recored, config_id)
            synchronize_id.action_create_api_synchronize(
                payload=payload,
                model=model
            )
        return

    def action_write_api_synchronize(self, payload=False, model=False):
        if not payload:
            return
        for synchronize_id in self:
            # get url api
            url = self.env.ref(
                'api_restful.default_api_restfull_url_config',
                False)
            if url:
                url = url.value + '/' + model
                url += '/' + str(synchronize_id.res_id_syn) + '/write'

            # get url access_token
            access_token = self.env.ref(
                'api_restful.default_api_restfull_access_token_config',
                False)

            headers = {
                'content-type': 'application/json',
                'access-token': access_token and access_token.value or False,
            }
            # # call api
            response = requests.request(
                "PATCH",
                url,
                data=json.dumps(payload),
                headers=headers
            )

            synchronize_line_id = synchronize_id.line_ids. \
                filtered(lambda x: x.state in ['waiting', 'failed'] and \
                                   x.slc_method == 'put'). \
                sorted(key=lambda l: l.write_date)

            # 200 - synchronize done
            if not synchronize_line_id:
                synchronize_line_id = self.env['api.synchronize.data.line'].create({
                    'synchronize_id': synchronize_id.id,
                    'slc_method': 'put',
                    'result': 'Waiting',
                    'state': 'waiting'
                })
            result = response.text
            if response.status_code not in [200] or response.status_code in [200] and 'error' in result:
                synchronize_id.write({
                    'result': response.text,
                    'state': 'failed',
                    'number_of_retries': synchronize_id.number_of_retries + 1
                })
                synchronize_line_id[-1].write({
                    'result': response.text,
                    'state': 'failed',
                    'payload': json.dumps(payload),
                })
            else:
                synchronize_id.write({
                    'state': 'done',
                    'number_of_retries': 0
                })
                # done line có slc_method put mới nhất
                synchronize_line_id[-1].write({
                    'result': 'done',
                    'state': 'done',
                    'payload': json.dumps(payload),
                })

                sync_rec_id = self.env[synchronize_id.model].browse(
                    synchronize_id.res_id)
                if 'sync_id' in dir(sync_rec_id) and not sync_rec_id.sync_id:
                    sync_rec_id.sync_id = synchronize_id.res_id_syn

                # xử lý faild line có slc_method put còn lại
                # synchronize_id.line_ids.\
                #     filtered(lambda x: x != synchronize_line_id[-1] and \
                #              x.slc_method == 'put' ).write({
                #     'state': 'failed',
                # })

    @api.model
    def cron_write_api_synchronize(self, model=False, limit=False):
        if not model:
            return
        limit = limit
        if not limit:
            limit = 500

        config_id = self.env['api.synchronize.data.config'].search([
            ('model', '=', model),
            ('state', '=', 'post'),
        ], limit=1)
        if not config_id:
            return

        # check synchronize Waiting
        synchronize_ids = self.env['api.synchronize.data'].search([
            ('model', '=', model),
            ('res_id', '!=', False),
            ('res_id_syn', '!=', False),
            ('state', 'in', ['waiting','failed']),
            ('slc_method', '=', 'put')
        ], limit=limit)

        res_ids = synchronize_ids.mapped('res_id')
        model_obj = self.env[model].with_context(active_test=False)
        record_ids = model_obj.search([('id', 'in', res_ids)], limit=limit)
        for record in record_ids:
            payload = self.prepare_payload(record, config_id)
            synchronize_id = synchronize_ids.\
                filtered(lambda x: x.res_id == record.id)
            synchronize_id.action_write_api_synchronize(
                payload=payload,
                model=model
            )

        return
