# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
import requests
import json
from datetime import datetime
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
URL_CONFIG = 'api_restful.default_api_restfull_url_config'
TOKEN_CONFIG = 'api_restful.default_api_restfull_access_token_config'


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


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def action_post(self):
        for payment in self:
            res = super(AccountPayment, self).action_post()
            if payment.state == 'posted':
                syn_pay_id = self.env['api.synchronize.data'].search([
                    ('type', '=', 'transaction'),
                    # ('state', '=', 'done'),
                    ('model', '=', self._name),
                    ('res_id', '=', self.id),
                ], limit=1)
                if syn_pay_id:
                    syn_pay_id.write({
                        'is_run': True,
                        'state': 'waiting',
                        'name': payment.display_name,
                    })
        return res

    def action_draft(self):
        for rec in self:
            res = super(AccountPayment, self).action_draft()
            if rec.state != 'done':
                syn_pay_id = self.env['api.synchronize.data'].search([
                    ('type', '=', 'transaction'),
                    # ('state', '=', 'done'),
                    ('model', '=', self._name),
                    ('res_id', '=', self.id),
                    ('res_id_syn', '!=', 0),
                ], limit=1)
                if syn_pay_id:
                    syn_pay_id.write({
                        'is_delete': True,
                        'state': 'waiting',
                        'slc_method': 'delete',
                        'is_run': False,
                    })
        return res

    def action_api_payment_delete(self):
        for pay in self:
            syn_id = self.env['api.synchronize.data'].search([
                ('type', '=', 'transaction'),
                # ('slc_method', '=', 'post'),
                ('state', '=', 'waiting'),
                ('model', '=', pay._name),
                ('res_id', '=', pay.id),
            ])
            if syn_id:
                pay.action_api_delete_restful_token(syn_id)

    def action_api_delete_restful_token(self, synchronize_id):
        """
        Phương thức này chỉ dành cho khế ước nên nếu sử dụng lại phải check quy trình
        khế ước bị ảnh hưởng không
        """
        for rcs in self:
            url = self.env.ref(
                'api_restful.default_api_restfull_url_config',
                False)
            if url:
                url = url.value + '/' + rcs._name
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
                synchronize_id.res_id_syn) + '/' + 'api_button_delete'
            response = requests.request(
                "PATCH",
                url,
                data=json.dumps(payload),
                headers=headers
            )
            if response.status_code in [200]:
                synchronize_id.unlink()

    def _get_default_header_request(self):
        url = self.env.ref(URL_CONFIG, False)
        access_token = self.env.ref(TOKEN_CONFIG, False)
        if not (url and access_token):
            return '', {}
        url = url.value + '/' + self._name
        return url, {
            'content-type': 'application/json',
            'access-token': access_token and access_token.value or False,
        }

    def _create_payment_vals_api(self):
        partner_id = self.env['api.synchronize.data'].search([
            ('model', '=', 'res.partner'),
            ('res_id', '=', self.partner_id.id),
        ])
        partner_bank_id = self.env['api.synchronize.data'].search([
            ('model', '=', 'res.partner.bank'),
            ('res_id', '=', self.partner_bank_id.id),
        ])
        currency_rate = self.currency_id.rate or 0
        # line_ids = self.env['account.move.line']
        # if self.payment_lines:
        #     line_ids = self.payment_lines.mapped('move_id.line_ids')
        # if self.move_line_ids:
        #     line_ids |= self.move_line_ids
        # if line_ids:
        #     currency_rate = line_ids and line_ids[0].currency_ex_rate != 0 and \
        #                     line_ids[0].currency_ex_rate or \
        #                     line_ids and line_ids[0].second_ex_rate or 0

        payment_vals = {
            'name': self.name,
            'payment_type': self.payment_type,
            'partner_type': self.partner_type,
            'partner_id': partner_id and partner_id.res_id_syn or False,
            'date': str(self.date),
            'amount': self.amount,
            'ref': self.ref,
            'responsible': self.responsible or '',

            'journal_id': self.journal_id and \
                          self.journal_id.sync_id or False,
            'currency_id': self.currency_id and \
                           self.currency_id.sync_id or False,

            'partner_bank_id': partner_bank_id and \
                               partner_bank_id.res_id_syn or False,

            # 'payment_method_id': self.payment_method_id.id,
            'analytic_account_id': self.account_analytic_id and \
                                   self.account_analytic_id.sync_id or False,
            # 'destination_account_id': self.destination_account_id and \
            #                           self.destination_account_id.sync_id or False,
            # 'writeoff_account_id': self.writeoff_account_id and \
            #                        self.writeoff_account_id.sync_id or False,
            'currency_rate': currency_rate,
            'conversion_currency_rate': currency_rate,
            'is_api': str(True),
            # 'payment_reference': self.source_document or '',
        }
        # if self.show_invoice:
        #     if self.payment_invoices:
        #         payment_vals.update({
        #             'amount': 0,
        #         })
        #     payment_vals.update({
        #         # 'show_invoice': self.show_invoice,
        #         'payment_invoices': self._prepare_payment_invoice_api(),
        #     })
        if self.payment_type == 'transfer':
            payment_vals.update({
                'payment_type': 'outbound',
                'is_internal_transfer': str('True'),
                'destination_account_id': self.destination_journal_id and \
                                          self.destination_journal_id.default_debit_account_id and \
                                          self.destination_journal_id.default_debit_account_id.sync_id or False
            })
        return payment_vals

    # def _prepare_payment_invoice_api(self):
    #     # values = [
    #     #     'account.move',
    #     #     (5, 0, 0)
    #     # ]
    #     values = []
    #     currency_rate = self.currency_id.rate or 0
    #     line_ids = self.env['account.move.line']
    #     if self.payment_lines:
    #         line_ids = self.payment_lines.mapped('move_id.line_ids')
    #     if self.move_line_ids:
    #         line_ids |= self.move_line_ids
    #     if line_ids:
    #         currency_rate = line_ids and line_ids[0].currency_ex_rate != 0 and \
    #                         line_ids[0].currency_ex_rate or \
    #                         line_ids and line_ids[0].second_ex_rate or 0
    #     for invoice in self.payment_invoices:
    #         if self.partner_type == 'customer':
    #             move_type = 'out_receipt'
    #             if self.payment_type == 'outbound':
    #                 move_type = 'in_receipt'
    #         if self.partner_type == 'supplier':
    #             move_type = 'in_receipt'
    #             if self.payment_type == 'inbound':
    #                 move_type = 'out_receipt'
    #
    #         values += [(0, 0, {
    #             'name': invoice.number or self.name,
    #             'payment_reference': self.communication,
    #             'ref': self.communication,
    #             'move_type': move_type,
    #             'currency_id': invoice.currency_id and invoice.currency_id.sync_id or False,
    #             'partner_id': invoice.partner_id and invoice.partner_id.sync_id or False,
    #             'journal_id': invoice.journal_id.sync_id,
    #             'date': self.payment_date or invoice.date or '',
    #             'invoice_date_due': self.payment_date or invoice.date or '',
    #             'invoice_date': invoice.date or '',
    #             'analytic_account_id': invoice.account_analytic_id and \
    #                                    invoice.account_analytic_id.sync_id or False,
    #             'currency_rate': currency_rate,
    #             'invoice_line_ids': invoice._prepare_invoice_line_api(),
    #
    #             # 'invoice_reference_v9': invoice.symbol_invoice or '',
    #             'invoice_number_v9': invoice.number or '',
    #             # 'denominator_invoice_v9': invoice.denominator_invoice or '',
    #             # 'tax_correction_v9': invoice.tax_correction,
    #             'invoice_origin': invoice.ref or '',
    #             # 'rate_type': invoice.move_id and invoice.move_id.line_ids[0].rate_type or ''
    #         })]
    #     return values

    def action_api_create(self, synchronize_id):
        url, headers = self._get_default_header_request()
        for rcs in self:
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
                payload = rcs._create_payment_vals_api()
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
                    'model_syn': rcs._name,
                    'name_syn': synchronize_value['result']['data']['data'][0]['display_name'],
                    'slc_method': 'post',
                    'result': 'Create Done',
                    'state': 'waiting',
                    'line_ids': [(0, 0, value)]
                })
            return synchronize_id

    def action_api_restful_token(self, synchronize_id):
        url, headers = self._get_default_header_request()
        # url += '/' + str(synchronize_id.res_id_syn) + '/' + 'action_post'
        url += '/' + str(synchronize_id.res_id_syn) + '/' + 'action_api_post'
        payload = {}
        response = requests.request("PATCH", url, data=json.dumps(payload), headers=headers)
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

    @api.model
    def cron_api_payment(self, from_date, to_date, limit, payment_type, partner_type):
        if not limit:
            limit = 100
        payment_ids = self.env['account.payment']
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
            payment_ids |= payment_ids.browse(synchronize_pay_ids.mapped('res_id'))
            limit = limit - len(payment_ids)
        if limit > 0:
            from_date = datetime.strptime(from_date, '%d/%m/%Y')
            from_date = datetime.strftime(from_date, DATE_FORMAT)
            domain = [
                ('date', '>=', from_date),
                ('state', '=', 'posted'),
                ('journal_id.is_api', '=', True),
                # ('operation_receipt_id', '=', False),
                # ('operation_payment_id', '=', False),
                # ('invoice_journal_id.is_api', '=', True),
            ]
            if to_date:
                to_date = datetime.strptime(to_date, '%d/%m/%Y')
                to_date = datetime.strftime(to_date, DATE_FORMAT)
                domain += [('date', '<=', to_date)]

            # Loc phiếu đã done
            if synchronize_done_ids:
                list_pay_ids += synchronize_done_ids.mapped('res_id')
            # Lọc phiếu pay faild
            if payment_ids:
                list_pay_ids += payment_ids.ids
            if list_pay_ids:
                domain += [('id', 'not in', list_pay_ids)]

            if payment_type:
                domain += [('payment_type', '=', payment_type)]
            if partner_type:
                domain += [('partner_type', '=', partner_type)]
            # domain = [('id', 'in', [37941, 37936, 37575])]
            payment_ids |= self.env['account.payment'].search(domain, limit=limit)
            # payment_ids = self.env['account.payment'].browse(40653)
        for payment in payment_ids:
            synchronize_id = synchronize_pay_ids.filtered(
                lambda x: x.res_id == payment.id and x.model == self._name)
            payment.action_api_script_pay(synchronize_id)
        return True

    def action_api_delete_base(self, synchronize_id):
        """
        """
        for rcs in self:
            url = self.env.ref(
                'api_restful.default_api_restfull_url_config',
                False)
            if url:
                url = url.value + '/' + rcs._name
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
                synchronize_id.res_id_syn) + '/' + 'api_button_delete'
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

    def action_api_script_pay(self, synchronize_id):
        for payment in self:
            if synchronize_id.is_delete and synchronize_id.res_id_syn:
                payment.action_api_delete_base(synchronize_id)
                if synchronize_id.is_run and not synchronize_id.is_delete:
                    synchronize_syn_id = payment.action_api_create(
                        synchronize_id)
                    if synchronize_syn_id and synchronize_syn_id.state != 'done' and \
                            synchronize_syn_id.slc_method in ['post', 'patch']:
                        payment.action_api_restful_token(synchronize_syn_id)
            elif synchronize_id.is_run:
                # run
                synchronize_syn_id = payment.action_api_create(
                    synchronize_id)
                if synchronize_syn_id and synchronize_syn_id.state != 'done' and \
                        synchronize_syn_id.slc_method in ['post', 'patch']:
                    payment.action_api_restful_token(synchronize_syn_id)
            else:
                synchronize_syn_id = payment.action_api_create(synchronize_id)
                if synchronize_syn_id and synchronize_syn_id.state != 'done' and \
                        synchronize_syn_id.slc_method in ['post', 'patch']:
                    payment.action_api_restful_token(synchronize_syn_id)


# class AccountMove(models.Model):
#     _inherit = "account.move"
#
#     def _prepare_invoice_line_api(self):
#         values = [(0, 0, self._prepare_invoice_line_api_line(invoice_line))
#                   for invoice_line in self.invoice_line_ids]
#         return values
#
#     def _prepare_invoice_line_api_line(self, invoice_line):
#         analytic_account_id = invoice_line.account_analytic_id \
#                               and invoice_line.account_analytic_id.sync_id or False
#         value = {
#             'name': invoice_line.name,
#             'quantity': invoice_line.quantity,
#             'price_unit': invoice_line.price_unit,
#             'account_id': invoice_line.account_id.sync_id,
#             'analytic_account_id': analytic_account_id,
#         }
#         if self.tax_ids:
#             value.update({
#                 'tax_ids': [(6, 0, self.tax_ids.mapped('sync_id'))],
#             })
#         return value
