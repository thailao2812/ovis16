# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
import requests
import json
from datetime import datetime

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class AccountCashOperation(models.Model):
    _inherit = "account.cash.operation"

    def _create_cash_vals_api(self):
        partner_id = self.env['api.synchronize.data'].search([
            ('model', '=', 'res.partner'),
            ('res_id', '=', self.partner_id.id),
        ])
        partner_bank_id = self.env['api.synchronize.data'].search([
            ('model', '=', 'res.partner.bank'),
            ('res_id', '=', self.partner_bank_id.id),
        ])
        cash_vals = {
            'name': self.name,
            'partner_id': partner_id and partner_id.res_id_syn or False,
            'partner_bank_id': partner_bank_id and \
                               partner_bank_id.res_id_syn or False,
            'day_count_basis': self.day_count_basis,
            'date_start': self.date_start,
            'date_stop': self.date_stop,
            'payment_date': self.payment_date or '',
            'amount_main': self.amount_main,
            'currency_id': self.currency_id and \
                           self.currency_id.sync_id or False,
            'rate': self.rate,
            'days': self.days,
            'rate_per_day': self.rate_per_day,
            'account_id': self.account_id and self.account_id.sync_id or False,
            'account_recognition_id': self.account_recognition_id and \
                                      self.account_recognition_id.sync_id or False,
            'payment_method_id': self.payment_method_id and \
                                 self.payment_method_id.sync_id or False,
            'description': self.description or '',
            'company_analytic_account_id': self.company_analytic_account_id and \
                                           self.company_analytic_account_id.sync_id or False,
            'analytic_account_id': self.account_analytic_id and \
                                   self.account_analytic_id.sync_id or False,
            'contract_number': self.name or '',
            '__api_boolean__is_api': str({
                'field': 'is_api',
                'value': True
            }),
        }
        if self.payment_lines:
            cash_vals.update({
                '__api__payment_lines': str(self._prepare_payment_payment_lines())
            })
        if self.operation_payment_lines:
            cash_vals.update({
                '__api__operation_payment_lines': str(
                    self._prepare_operation_payment_lines())
            })
        if self.operation_receipt_lines:
            cash_vals.update({
                '__api__operation_receipt_lines': str(
                    self._prepare_operation_receipt_lines())
            })
        return cash_vals

    def _prepare_payment_payment_lines(self):
        values = [
            'account.cash.operation.line',
            (5, 0, 0)
        ]
        for pay_line in self.payment_lines:
            syn_id = self.env['api.synchronize.data']
            if pay_line.payment_id:
                syn_id = pay_line.payment_id.action_api_create(syn_id)

            values_dict = {
                'name': pay_line.name,
                'payment_method_id': pay_line.payment_method_id and \
                                     pay_line.payment_method_id.sync_id or False,
                'date': pay_line.date,
                'loan_amount': pay_line.loan_amount,
                'days': pay_line.days,
                'rate_per_day': pay_line.rate_per_day,
                'amount': pay_line.amount,
                'actual_amount': pay_line.actual_amount,
                'cumulative_amount': pay_line.cumulative_amount,
                'sequence': pay_line.sequence,
                'currency_id': pay_line.currency_id and \
                               pay_line.currency_id.sync_id or False,
                'state': pay_line.state,
                'rate': self.rate,
            }
            if syn_id:
                values_dict.update({
                    'payment_id': syn_id.res_id_syn,
                })
            values += [(0, 0, values_dict)]

        return values

    def _prepare_operation_payment_lines(self):
        values = [
            'account.cash.operation.in.out',
            (5, 0, 0)
        ]
        for pay_line in self.operation_payment_lines:
            syn_id = self.env['api.synchronize.data']
            if pay_line.payment_id:
                syn_id = pay_line.payment_id.action_api_create(syn_id)
            values_dict = {
                'name': pay_line.name,
                'payment_method_id': pay_line.payment_method_id and \
                                     pay_line.payment_method_id.sync_id or False,
                'date': pay_line.date,
                'amount': pay_line.amount,
                'payment_type': pay_line.payment_type,
                'currency_id': pay_line.currency_id and \
                               pay_line.currency_id.sync_id or False,
                'state': pay_line.state,
            }
            if syn_id:
                values_dict.update({
                    'payment_id': syn_id.res_id_syn,
                })

            values += [(0, 0, values_dict)]
        return values

    def _prepare_operation_receipt_lines(self):
        values = [
            'account.cash.operation.in.out',
            (5, 0, 0)
        ]
        for pay_line in self.operation_receipt_lines:
            syn_id = self.env['api.synchronize.data']
            if pay_line.payment_id:
                syn_id = pay_line.payment_id.action_api_create(syn_id)
            values_dict = {
                'name': pay_line.name,
                'payment_method_id': pay_line.payment_method_id and \
                                     pay_line.payment_method_id.sync_id or False,
                'date': pay_line.date,
                'amount': pay_line.amount,
                'payment_type': pay_line.payment_type,
                'currency_id': pay_line.currency_id and \
                               pay_line.currency_id.sync_id or False,
                'state': pay_line.state,
            }
            if syn_id:
                values_dict.update({
                    'payment_id': syn_id.res_id_syn,
                })
            values += [(0, 0, values_dict)]
        return values

    @api.model
    def cron_api_account_cash_operation(self, type, limit):
        if not limit:
            limit = 100
        cash_ids = self.env['account.cash.operation']
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
            cash_ids |= synchronize_pay_ids.mapped('reference')
            limit = limit - len(cash_ids)
        if limit > 0:
            domain = []
            # Loc phiếu đã done
            if synchronize_done_ids:
                list_pay_ids += synchronize_done_ids.mapped('reference').ids
            # Lọc phiếu pay faild
            if cash_ids:
                list_pay_ids += cash_ids.ids
            if list_pay_ids:
                domain += [('id', 'not in', list_pay_ids)]

            # domain = [('id', 'in', [39])]
            cash_ids |= self.env[self._name].search(domain, limit=limit)
        for cash in cash_ids:
            synchronize_id = synchronize_pay_ids.filtered(
                lambda x: x.res_id == cash.id and x.model == self._name)
            cash.action_api_script(synchronize_id)
        return True

    @api.model
    def cron_api_account_cash_operation_delete(self, type, limit):
        if not limit:
            limit = 100
        synchronize_pay_ids = self.env['api.synchronize.data'].search([
            ('type', '=', 'transaction'),
            ('state', '=', 'failed'),
            ('model', '=', 'account.cash.operation'),
            ('res_id_syn', '!=', False),
        ], limit=limit)

        for syn in synchronize_pay_ids:
            syn.reference.action_api_delete_restful_token(syn)

        synchronize_pay_ids = self.env['api.synchronize.data'].search([
            ('type', '=', 'transaction'),
            ('state', '=', 'failed'),
            ('model', '=', self._name),
            ('res_id_syn', '=', False),
        ], limit=limit)
        if synchronize_pay_ids:
            cash_id = synchronize_pay_ids.mapped('reference')
            # update lại các synchronize payment đã done
            payment_ids = self.env['account.payment']
            if cash_id and cash_id.payment_lines:
                payment_ids |= cash_id.payment_lines.mapped('payment_id')
            if cash_id and  cash_id.operation_payment_lines:
                payment_ids |= cash_id.operation_payment_lines.mapped(
                    'payment_id')
            if cash_id and  cash_id.operation_receipt_lines:
                payment_ids |= cash_id.operation_receipt_lines.mapped(
                    'payment_id')

            for payment in payment_ids:
                payment.action_api_payment_delete()

        return True

    def action_api_create(self, synchronize_id):
        for rcs in self:
            url = self.env.ref(
                'api_restful.default_api_restfull_url_config',
                False)
            if url:
                url = url.value + '/' + 'account.cash.operation'
            # get url access_token
            access_token = self.env.ref(
                'api_restful.default_api_restfull_access_token_config',
                False)
            headers = {
                'content-type': 'application/x-www-form-urlencoded',
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
                payload = rcs._create_cash_vals_api()
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
                synchronize_id.write({
                    'res_id_syn': synchronize_value['data'][0]['id'],
                    'model_syn': rcs._name,
                    'name_syn': synchronize_value['data'][0]['name'],
                    'slc_method': 'post',
                    'result': 'Create Done',
                    'state': 'waiting',
                    'line_ids': [(0, 0, value)]
                })
            return synchronize_id

    def action_api_delete_restful_token(self, synchronize_id):
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
                'content-type': 'application/x-www-form-urlencoded',
                'access-token': access_token and access_token.value or False,
            }
            # call api action done của stock.picking
            payload = {}
            url += '/' + str(
                synchronize_id.res_id_syn) + '/' + 'api_button_cash_delete'
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
                cash_id = synchronize_id.mapped('reference')
                # update lại các synchronize payment đã done
                payment_ids = self.env['account.payment']
                if cash_id.payment_lines:
                    payment_ids |= cash_id.payment_lines.mapped('payment_id')
                if cash_id.operation_payment_lines:
                    payment_ids |= cash_id.operation_payment_lines.mapped(
                        'payment_id')
                if cash_id.operation_receipt_lines:
                    payment_ids |= cash_id.operation_receipt_lines.mapped(
                        'payment_id')
                if payment_ids:
                    self.action_api_payment_delete(payment_ids)
                synchronize_id.unlink()

    def action_api_payment_delete(self, payment_ids):
        for pay in payment_ids:
            syn_id = self.env['api.synchronize.data'].search([
                ('type', '=', 'transaction'),
                # ('slc_method', '=', 'post'),
                # ('state', '=', 'waiting'),
                ('model', '=', pay._name),
                ('res_id', '=', pay.id),
            ])
            if syn_id:
                syn_id.unlink()

    def action_api_restful_token(self, synchronize_id):
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
                'content-type': 'application/x-www-form-urlencoded',
                'access-token': access_token and access_token.value or False,
            }
            # call api action done của stock.picking
            payload = {}
            # url += '/' + str(synchronize_id.res_id_syn) + '/' + '_action_done'
            if self.state == 'confirm':
                url += '/' + str(
                    synchronize_id.res_id_syn) + '/' + 'api_button_confirm'
            else:
                url += '/' + str(
                    synchronize_id.res_id_syn) + '/' + 'api_button_done'

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
                    'line_ids': [(0, 0, value)]
                })

                cash_id = synchronize_id.mapped('reference')
                # update lại các synchronize payment đã done
                payment_ids = self.env['account.payment']
                if cash_id.payment_lines:
                    payment_ids |= cash_id.payment_lines.mapped('payment_id')
                if cash_id.operation_payment_lines:
                    payment_ids |= cash_id.operation_payment_lines.mapped('payment_id')
                if cash_id.operation_receipt_lines:
                    payment_ids |= cash_id.operation_receipt_lines.mapped('payment_id')
                if payment_ids:
                    self.action_api_payment_done(payment_ids)

    def action_api_payment_done(self, payment_ids):
        for pay in payment_ids:
            syn_id = self.env['api.synchronize.data'].search([
                ('type', '=', 'transaction'),
                ('slc_method', '=', 'post'),
                ('state', '=', 'waiting'),
                ('model', '=', pay._name),
                ('res_id', '=', pay.id),
            ])
            if syn_id:
                value = {
                    'slc_method': 'patch',
                    'payload': '',
                    'result': 'done',
                    'state': 'done',
                }
                syn_id.write({
                    'result': 'Action Cash Done',
                    'state': 'done',
                    'line_ids': [(0, 0, value)]
                })

    def action_api_script(self, synchronize_id):
        for cash in self:
            if synchronize_id.is_delete and synchronize_id.res_id_syn:
                cash.action_api_delete_picking(synchronize_id)
                if synchronize_id.is_run and not synchronize_id.is_delete:
                    synchronize_syn_id = cash.action_api_create(
                        synchronize_id, 'in')
                    if synchronize_syn_id and synchronize_syn_id.state != 'done' and \
                            synchronize_syn_id.slc_method in ['post', 'patch']:
                        cash.action_api_restful_token(synchronize_syn_id)
            elif synchronize_id.is_run:
                synchronize_syn_id = cash.action_api_create(
                    synchronize_id, 'in')
                if synchronize_syn_id and synchronize_syn_id.state != 'done' and \
                        synchronize_syn_id.slc_method in ['post', 'patch']:
                    cash.action_api_restful_token(synchronize_syn_id)
            else:
                synchronize_syn_id = cash.action_api_create(synchronize_id)
                if synchronize_syn_id and synchronize_syn_id.state != 'done' and \
                        synchronize_syn_id.slc_method in ['post', 'patch']:
                    cash.action_api_restful_token(synchronize_syn_id)
