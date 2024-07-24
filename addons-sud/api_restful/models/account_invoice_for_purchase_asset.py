# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
import requests
import json
from datetime import datetime
from api_default_method import (
    default_create_value, get_default_header_request, format_date_format
)
from account_payment import (
    pre_synchronize_value, request_api, pre_create_sync_value
)
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class AccountInvoicePurchaseAsset(models.Model):
    _inherit = "account.invoice"

    def create_invoice_purchase(self):
        url, headers = get_default_header_request(self)
        url = url.replace(self._name, 'account.move')
        api_sync_obj = self.env['api.synchronize.data'].sudo()
        synchronize_id = api_sync_obj.search(
            [('type', 'in', ['transaction']),
             ('res_id', '=', self.id),
             ('model', '=', self._name)])
        if synchronize_id.state == 'done':
            return synchronize_id
        if not synchronize_id:
            synchronize_id = api_sync_obj.create(
                default_create_value(self, 'transaction'))
        payload = self._prepare_invoice_purchase_val()
        response = request_api("POST", url, payload, headers)
        if response.status_code not in [200]:
            synchronize_id.write(pre_synchronize_value(payload, response))
            return synchronize_id
        pre_sync_value = pre_create_sync_value(self._name, payload, response)
        pre_sync_value.update({'model_syn': 'account.move'})
        if self.state == 'draft':
            synchronize_id.write(pre_sync_value)
            return synchronize_id
        _url = url + '/' + str(pre_sync_value['res_id_syn']) + '/post'
        response = request_api("PATCH", _url, {}, headers)
        pre_sync_value_patch = pre_synchronize_value({}, response)
        if pre_sync_value_patch.get('line_ids', False):
            pre_sync_value_patch['line_ids'] = pre_sync_value.get(
                'line_ids', []) + pre_sync_value_patch['line_ids']
        pre_sync_value.update(pre_sync_value_patch)
        synchronize_id.write(pre_sync_value)
        return synchronize_id

    def _prepare_invoice_purchase_val(self):
        values = [(0, 0, self._prepare_invoice_purchase_line_val(x))
                  for x in self.invoice_line_ids]
        if self.env.context.get('not_asset', False):
            type = 'in_receipt'
        else:
            type = self.type

        return {
            'create_from_purchase_invoice': True,
            'name': self.number,
            'move_type': type,
            'currency_id': self.currency_id and self.currency_id.sync_id or False,
            'partner_id': self.partner_id and self.partner_id.sync_id or False,
            'journal_id': self.journal_id.sync_id,
            'payment_reference': self.name,
            'date': self.date_invoice or '',
            'invoice_date_due': self.date_due or '',
            'invoice_date': self.supplier_inv_date or '',
            'analytic_account_id': self.account_analytic_id and \
                                   self.account_analytic_id.sync_id or False,
            'currency_rate': self._prepare_currency_rate(),
            '__api__invoice_line_ids': str(
                ['account.move.line', (5, 0, 0)] + values),

            # field dac thu da duoc them ở odoo 14
            'denominator_invoice_v9': self.denominator_invoice or '',
            'invoice_reference_v9': self.symbol_invoice or '',
            'invoice_number_v9': self.reference or '',
            'tax_correction_v9': self.amount_tax or '',
        }

    def _prepare_invoice_purchase_line_val(self, invoice_line):
        tax_ids = invoice_line.invoice_line_tax_ids
        if len(invoice_line.invoice_line_tax_ids) > 1:
            tax_ids = tax_ids.filtered(lambda x: x.amount != 0)
        return {
            'name': invoice_line.name,
            'quantity': invoice_line.quantity,
            'price_unit': invoice_line.price_unit,
            'account_id': invoice_line.account_id.sync_id,
            'analytic_account_id': invoice_line.account_analytic_id.sync_id,
            'price_subtotal': invoice_line.price_subtotal,
            'tax_ids': [(6, 0,
                         tax_ids and tax_ids[0].mapped('sync_id') or [])],
        }

    def _prepare_currency_rate(self):
        if self.currency_rate:
            return self.currency_rate
        action = self.action_view_move_line()
        domain = action.get('domain', [])
        lines = self.env['account.move.line'].search(domain)
        if lines:
            return lines[0].currency_ex_rate or lines[0].second_ex_rate
        return 0

    @api.model
    def cron_create_invoice_not_asset(self, date_from, date_to, limit=100):
        if not limit:
            limit = 100
        records = self.browse()
        date_from = format_date_format(date_from)
        date_to = format_date_format(date_to)
        fail_records = self.search(
            [('id', 'in', self._get_fail_sync_ids(date_from, date_to))],
            limit=limit)
        limit = limit - len(fail_records)
        if limit > 0:
            records |= fail_records
            records |= self.search(
                [('type', 'in', ('in_invoice', 'in_refund')),
                 ('journal_id.type', '=', 'general'),
                 ('date_invoice', '>=', date_from),
                 ('date_invoice', '<=', date_to),
                 ('id', 'not in', self._get_done_sync_ids())], limit=limit)
        for rec in records:
            rec.with_context(not_asset=True).create_invoice_purchase()

    def _get_done_sync_ids(self):
        done_sync_ids = self.env['api.synchronize.data'].search(
            [('type', '=', 'transaction'),
             ('state', '=', 'done'),
             ('model', '=', self._name)])
        purchase_asset_ids = self.env['account.asset.asset'].search([])
        return list(set(done_sync_ids.mapped('res_id') +
                        purchase_asset_ids.mapped('invoice_id').ids))

    def _get_default_records(self, date_from, date_to):
        records = self.search([('type', 'in', ('in_invoice', 'in_refund')),
                               ('date_invoice', '>=', date_from),
                               ('date_invoice', '<=', date_to),
                               ('journal_id.type', '=', 'general')])
        return records.ids

    def _get_fail_sync_ids(self, date_from, date_to):
        fail_sync_ids = self.env['api.synchronize.data'].search(
            [('type', '=', 'transaction'),
             ('state', '=', 'failed'),
             ('slc_method', '=', 'post'),
             ('res_id', 'in', self._get_default_records(date_from, date_to)),
             ('model', '=', self._name)])
        return fail_sync_ids.mapped('res_id')
