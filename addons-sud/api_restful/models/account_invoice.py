# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import requests
import json
from datetime import datetime
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

value_write = [
    'status', 'ref_id', 'invoice_number', 'invoice_issue_date',
    'org_invoice_number', 'org_invoice_issued_date', 'type_invoice',
    'ref_type', 'transaction_id'
]


class AccountMove(models.Model):
    _inherit = "account.move"

    def write(self, vals):
        res = super(AccountMove, self).write(vals)
        for rcs in self:
            sql = '''
                    SELECT id
                    FROM api_synchronize_data
                    WHERE model = '%(model)s'
                    AND res_id = %(res_id)s
                    AND state = 'done'
                    ''' % ({
                'model': rcs._name,
                'res_id': rcs.id,
            })
            self.env.cr.execute(sql)
        for synchronize in self.env.cr.dictfetchall():
            # if any(field in value_write for field in vals):
            synchronize_id = self.env['api.synchronize.data'].sudo().browse(
                synchronize['id'])
            # create data line để đợi update
            self.env['api.synchronize.data.line'].create({
                'synchronize_id': synchronize_id.id,
                'slc_method': 'put',
                'result': 'Waiting',
                'state': 'waiting'
            })
            synchronize_id.write({
                'state': 'waiting',
                'result': 'Waiting',
                'is_write': True,
            })
        return res

    def _prepare_invoice_api_write(self):
        self.ensure_one()
        # journal = self.env['account.move'].with_context(default_move_type='out_invoice')._get_default_journal()

        invoice_vals = {
            # field dac thu da duoc them ở odoo 14
            'status': self.status or '',
            'ref_id': self.ref_id or '',
            'invoice_number': self.invoice_number or '',
            'invoice_issue_date': self.invoice_issue_date or '',
            'org_invoice_number': self.org_invoice_number or '',
            'org_invoice_issued_date': self.org_invoice_issued_date or '',
            'type_invoice': self.type_invoice or '',
            'ref_type': self.ref_type or '',

            # field char
            'transaction_id': self.transaction_id or '',
        }
        return invoice_vals

    def _prepare_invoice_api(self):
        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        self.ensure_one()
        # journal = self.env['account.move'].with_context(default_move_type='out_invoice')._get_default_journal()
        # partner_id = self.env['api.synchronize.data'].search([
        #     ('model', '=', 'res.partner'),
        #     ('res_id', '=', self.partner_id.id),
        # ])
        invoice_vals = {
            'name': self.name or '',
            'ref': self.ref or '',
            'move_type': self.move_type,
            'currency_id': self.currency_id and self.currency_id.sync_id or False,
            # 'partner_id': partner_id and partner_id.res_id_syn or False,
            'partner_id': self.partner_id.sync_id or False,
            'journal_id': self.journal_id.sync_id or False,
            'date': str(self.date) or '',
            'invoice_date_due': str(self.invoice_date_due) or '',
            'invoice_date': str(self.date) or '',
            'analytic_account_id': self.account_analytic_id and \
                                   self.account_analytic_id.sync_id or False,
            'inv_type': self.trans_type or False,
            'currency_rate': self.currency_rate or False,

            # field dac thu da duoc them ở odoo 14
            'status': self.status or '',
            'ref_id': self.ref_id or '',
            'invoice_number': self.invoice_number or '',
            'invoice_issue_date': self.invoice_issue_date or '',
            'org_invoice_number': self.org_invoice_number or '',
            'org_invoice_issued_date': self.org_invoice_issued_date or '',
            'type_invoice': self.type_invoice or '',
            'ref_type': self.ref_type or '',
            # field char
            'transaction_id': self.transaction_id or '',

            # field price_unit v9 đề dùm cho tool giá thành
            # 'price_v9': self.stock_move_id and \
            #             self.stock_move_id.price_unit or 0,
            # ------------------------------------------------------
            'payment_reference': self.name or '',
            'invoice_origin': self.origin or '',
            'commercial_name': self.commercial_name or '',
            'payment_reference': self.payment_reference or '',
            # ------------------------------------------------------
            # 'rate_type': self.move_id and self.move_id.line_ids[0].rate_type or '',
        }
        return invoice_vals

    def _prepare_invoice_line_api(self):
        values = []
        for invoice_line in self.invoice_line_ids:
            product_id = self.env['api.synchronize.data'].search([
                ('model', '=', 'product.template'),
                ('res_id', '=', invoice_line.product_id.product_tmpl_id.id),
            ])
            # move_line = self.move_id.line_ids.filtered(
            #     lambda x: x.account_id == invoice_line.account_id)
            tax_ids = invoice_line.tax_ids.mapped('sync_id')
            values += [(0, 0, {
                'sequence': invoice_line.sequence,
                'name': invoice_line.name,
                'product_id': product_id.res_id_syn or False,
                'product_uom_id': invoice_line.product_uom_id.sync_id or False,
                'quantity': invoice_line.quantity,
                'discount': invoice_line.discount,
                'price_unit': invoice_line.price_unit,
                'account_id': invoice_line.account_id.sync_id or False,
                'tax_ids': [(6, 0, invoice_line.tax_ids.mapped('sync_id'))] if tax_ids else '',
                # 'rate_type': move_line and move_line[0].rate_type or '',
            })]
        return values

    def action_api_write_invoice(self, synchronize_id):
        for rcs in self:
            url = self.env.ref(
                'api_restful.default_api_restfull_url_config',
                False)
            if url:
                url = url.value + '/' + synchronize_id.model_syn
                url += '/' + str(synchronize_id.res_id_syn) + '/' + 'write'

            # get url access_token
            access_token = self.env.ref(
                'api_restful.default_api_restfull_access_token_config',
                False)
            headers = {
                'content-type': 'application/json',
                'access-token': access_token and access_token.value or False,
            }
            if synchronize_id.is_write:
                # call api
                payload = rcs._prepare_invoice_api_write()
                payload = json.dumps(payload)
                response = requests.request(
                    "PATCH",
                    url,
                    data=payload,
                    headers=headers
                )
                synchronize_line_id = synchronize_id.line_ids. \
                    filtered(lambda x: x.state in ['waiting', 'failed'] and \
                                       x.slc_method == 'put'). \
                    sorted(key=lambda l: l.write_date)

                synchronize_value = json.loads(str(response.text))
                if response.status_code not in [200] or response.status_code in [200] and \
                        ('error' in synchronize_value[
                            'result'] if 'result' in synchronize_value else 'error' in synchronize_value):
                    synchronize_id.write({
                        'result': response.text,
                        'state': 'failed',
                    })
                    synchronize_line_id[-1].write({
                        'result': response.text,
                        'state': 'failed',
                        'payload': json.dumps(payload),
                    })
                else:
                    synchronize_id.write({
                        'slc_method': 'put',
                        'result': 'Write Done',
                        'state': 'done',
                        'is_write': False,
                    })
                    synchronize_line_id[-1].write({
                        'result': 'done',
                        'state': 'done',
                        'payload': json.dumps(payload),
                    })
            return synchronize_id

    def action_api_create_invoice(self, synchronize_id):
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
            if not synchronize_id:
                synchronize_id = self.env['api.synchronize.data'].create({
                    'name': rcs.name or '',
                    'model': rcs._name,
                    'res_id': rcs.id,
                    'type': 'transaction',
                    'slc_method': 'post',
                })

            if not synchronize_id.res_id_syn:
                # call api
                payload = self._prepare_invoice_api()
                payload.update({
                    'invoice_line_ids': self._prepare_invoice_line_api()
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
                synchronize_id.write({
                    'res_id_syn': synchronize_value['result']['data']['data'][0]['id'],
                    'model_syn': 'account.move',
                    'name_syn': synchronize_value['result']['data']['data'][0]['display_name'],
                    'slc_method': 'post',
                    'result': 'Create Done',
                    'state': 'waiting',
                    'line_ids': [(0, 0, value)]
                })
            return synchronize_id

    def action_api_restful_token(self, synchronize_id):
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
            # call api action done của stock.picking
            payload = {}
            payload = json.dumps(payload)
            url += '/' + str(synchronize_id.res_id_syn) + '/' + 'action_api_cron_done'
            response = requests.request(
                "PATCH",
                url,
                data=payload,
                headers=headers
            )
            synchronize_value = json.loads(str(response.text))
            if response.status_code not in [200] or response.status_code in [200] and\
                    ('error' in synchronize_value['result'] if 'result' in synchronize_value else 'error' in synchronize_value):
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

    def action_api_delete_invoice(self, synchronize_id):
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
            # call api action done của stock.picking
            payload = {}
            payload = json.dumps(payload)
            url += '/' + str(synchronize_id.res_id_syn) + '/' + 'action_api_delete'
            response = requests.request(
                "PATCH",
                url,
                data=payload,
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

    @api.model
    def cron_api_invoice(self, from_date, to_date, limit, type_invoice):
        if not limit:
            limit = 100
        invoice_ids = self.env['account.move']
        invoice_done_ids = self.env['account.move']
        # lấy lại các invoice bị faild và cron lại 1 lần nữa
        # bao gom cac
        synchronize_invoice_ids = self.env['api.synchronize.data'].search([
            ('type', 'in', ['transaction']),
            ('state', '!=', 'done'),
            ('model', '=', self._name),
        ], limit=limit)

        if synchronize_invoice_ids:
            invoice_ids |= invoice_ids.browse(synchronize_invoice_ids.mapped('res_id'))
            limit = limit - len(invoice_ids)

        # lấy các invoice đã đồng bộ thành công
        synchronize_invoice_done_ids = self.env['api.synchronize.data'].search([
            ('type', '=', 'transaction'),
            ('state', '=', 'done'),
            ('model', '=', self._name),
        ])

        if synchronize_invoice_done_ids:
            invoice_done_ids |= invoice_done_ids.browse(synchronize_invoice_done_ids.mapped('res_id'))

        if limit > 0:
            from_date = datetime.strptime(from_date, '%d/%m/%Y')
            from_date = datetime.strftime(from_date, DATE_FORMAT)
            domain = [
                ('state', 'in', ['draft', 'posted']),

                ('date', '>=', from_date),
                ('journal_id.is_api', '=', True),
            ]
            if to_date:
                to_date = datetime.strptime(to_date, '%d/%m/%Y')
                to_date = datetime.strftime(to_date, DATE_FORMAT)
                domain += [('date', '<=', to_date)]
            if type_invoice:
                domain += [('move_type', '=', type_invoice), ]
            else:
                domain += [('move_type', 'in', ['out_refund', 'out_invoice']), ]
            invoice_no_ids = invoice_ids and invoice_ids.ids or []
            invoice_no_ids += invoice_done_ids and invoice_done_ids.ids or []
            if invoice_no_ids:
                domain += [('id', 'not in', invoice_no_ids)]

            invoice_ids |= self.env['account.move'].search(domain, limit=limit)
            # invoice_ids = self.env['account.move'].browse(226385)
        for invoice in invoice_ids:
            try:
                synchronize_id = synchronize_invoice_ids.filtered(
                    lambda x: x.res_id == invoice.id and x.model == self._name)
                invoice.action_api_script_out(synchronize_id)
                self.env.cr.commit()
            except Exception as e:
                return str(e)
        return True

    def action_api_script_out(self, synchronize_id):
        for invoice in self:
            if synchronize_id.is_write:
                # write
                synchronize_syn_id = invoice.action_api_write_invoice(synchronize_id)
                # run
                if synchronize_id.state == 'done' and \
                        synchronize_id.slc_method == 'put':
                    invoice.action_api_restful_token(synchronize_syn_id)
            elif synchronize_id.is_delete and synchronize_id.res_id_syn:
                # delete
                invoice.action_api_delete_invoice(synchronize_id)
                if synchronize_id.is_run and not synchronize_id.is_delete:
                    synchronize_syn_id = invoice.action_api_create_invoice(
                        synchronize_id)
                    # create and run
                    if synchronize_syn_id and synchronize_syn_id.state != 'done' and \
                            synchronize_syn_id.slc_method in ['post', 'patch']:
                        invoice.action_api_restful_token(synchronize_syn_id)
            elif synchronize_id.is_run:
                # run
                synchronize_syn_id = invoice.action_api_create_invoice(
                    synchronize_id)
                if synchronize_syn_id and synchronize_syn_id.state != 'done' and \
                        synchronize_syn_id.slc_method in ['post', 'patch']:
                    invoice.action_api_restful_token(synchronize_syn_id)
            else:
                # create and run
                synchronize_syn_id = invoice.action_api_create_invoice(
                    synchronize_id)
                if synchronize_syn_id and synchronize_syn_id.state != 'done' and \
                        synchronize_syn_id.slc_method in ['post', 'patch']:
                    invoice.action_api_restful_token(synchronize_syn_id)

    def button_cancel(self):
        res = super(AccountMove, self).button_cancel()
        if self.state == 'cancel':
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

    # def invoice_validate(self):
    #     res = super(AccountMove, self).invoice_validate()
    #     for rcs in self:
    #         if rcs.state == 'open':
    #             syn_invoice_done_ids = self.env['api.synchronize.data'].search([
    #                 ('type', '=', 'transaction'),
    #                 ('slc_method', '=', 'delete'),
    #                 ('res_id', '=', rcs.id),
    #                 ('model', '=', rcs._name),
    #             ], limit=1)
    #             if syn_invoice_done_ids:
    #                 syn_invoice_done_ids.write({
    #                     'is_run': True,
    #                     'state': 'waiting',
    #                 })
    #     return res

    def action_api_update_invoice(self, synchronize_id):
        for rcs in self:
            url = self.env.ref(
                'api_restful.default_api_restfull_url_config',
                False)
            if url:
                url = url.value + '/' + synchronize_id.model_syn
                url += '/' + str(synchronize_id.res_id_syn) + '/' + 'write'
            # get url access_token
            access_token = self.env.ref(
                'api_restful.default_api_restfull_access_token_config',
                False)
            headers = {
                'content-type': 'application/json',
                'access-token': access_token and access_token.value or False,
            }

            if synchronize_id.res_id_syn:
                # call api
                payload = {
                    # 'rate_type': rcs.move_id.line_ids[0].rate_type,
                    # 'currency_rate': rcs.currency_rate,
                    'ref': rcs.ref or '',
                }
                payload = json.dumps(payload)
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
                synchronize_id.write({
                    'res_id_syn': synchronize_value['result']['data']['data'][0]['id'],
                    # 'model_syn': 'account.move',
                    'name_syn': synchronize_value['result']['data']['data'][0]['display_name'],
                    'slc_method': 'put',
                    'result': 'Update Done',
                    'state': 'done',
                    'line_ids': [(0, 0, value)]
                })
            return synchronize_id

    @api.model
    def cron_api_invoice_update(self, limit, type_invoice):
        if not limit:
            limit = 100

        # lấy các invoice đã đồng bộ thành công
        synchronize_invoice_done_ids = self.env['api.synchronize.data'].search([
            ('type', '=', 'transaction'),
            ('state', '=', 'waiting'),
            ('model', '=', self._name),
            ('res_id_syn', '!=', 0),
        ], limit=limit)
        invoice_ids = self.env['account.move'].browse(synchronize_invoice_done_ids.mapped('res_id'))
        # invoice_ids = self.env['account.move'].browse(226385)
        for invoice in invoice_ids:
            synchronize_id = synchronize_invoice_done_ids.filtered(
                lambda x: x.res_id == invoice.id and x.model == self._name)
            invoice.action_api_update_invoice(synchronize_id)
        return True