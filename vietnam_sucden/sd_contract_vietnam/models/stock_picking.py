# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

from datetime import datetime
import time

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%d-%m-%Y"
DAT = "%Y-%m-%d"


class StockPicking(models.Model):
    _inherit = "stock.picking"

    # def name_get(self):
    #     result = []
    #     if self.env.context.get('grn_fot_allocation'):
    #         for rec in self:
    #             if rec.picking_type_id.operation == 'station':
    #                 result.append((rec.id, rec.description_name))
    #             else:
    #                 result.append((rec.id, rec.name))
    #     else:
    #         for rec in self:
    #             result.append((rec.id, rec.name))
    #     return result

    # @api.model
    # def name_search(self, name='', args=None, operator='ilike', limit=100):
    #     args = args or []
    #     domain = []
    #     args += ['|',('name', operator, name), ('description_name',operator, name)]
    #     backorder = self.search(args + domain, limit=limit)
    #     if self._context.get('back_order'):
    #         domain = [('picking_type_id.code','=','incoming'),
    #                   ('picking_type_id.operation','=','factory'),
    #                   ('partner_id', '=', self._context.get('partner_id')),
    #                   ('date_done', '>=', self._context.get('date_done')),
    #                   ('backorder_id', '=', False)]
    #         backorder = self.search(args + domain, limit=limit)
    #     if self._context.get('purchase_contract_id') and self._context.get('grn_done'):
    #         purchase_contract = self.env['purchase.contract'].browse(self._context.get('purchase_contract_id'))
    #         grn_ids = purchase_contract.mapped('request_payment_ids').filtered(lambda x: int(x.name) < int(self._context.get('sequence'))).mapped('grn_done_ids').ids
    #         domain += [('warehouse_id.code', 'in', ['FA', 'KTN-LT-N', 'KTN-AP-N']),
    #                    ('partner_id', '=', purchase_contract.partner_id.id),
    #                    ('state', '=', 'done'), ('picking_type_id.operation', '=', 'factory'),
    #                    ('product_id', '=', purchase_contract.product_id.id),
    #                    ('id', 'not in', grn_ids)]
    #         backorder = self.search(args + domain, limit=limit)
    #     if self._context.get('purchase_contract_id') and self._context.get('grn_ready'):
    #         purchase_contract = self.env['purchase.contract'].browse(self._context.get('purchase_contract_id'))
    #         domain += [('warehouse_id.code', 'in', ['FA', 'KTN-LT-N', 'KTN-AP-N']),
    #                    ('partner_id', '=', purchase_contract.partner_id.id),
    #                    ('state', 'not in', ['done', 'cancel', 'draft']), ('picking_type_id.operation', '=', 'factory'),
    #                    ('product_id', '=', purchase_contract.product_id.id)]
    #         backorder = self.search(args + domain, limit=limit)
    #     if self._context.get('purchase_contract_id') and self._context.get('grn_fot_done'):
    #         purchase_contract = self.env['purchase.contract'].browse(self._context.get('purchase_contract_id'))
    #         domain += [('warehouse_id.code', 'in', ['FA']),
    #                    ('partner_id', '=', purchase_contract.partner_id.id),
    #                    ('state', '=', 'done'), ('picking_type_id.operation', '=', 'station'),
    #                    ('product_id', '=', purchase_contract.product_id.id)]
    #         backorder = self.search(args + domain, limit=limit)
    #     return backorder.name_get()

    # @api.model
    # def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
    #     if self._context.get('purchase_contract_id') and self._context.get('grn_done'):
    #         purchase_contract = self.env['purchase.contract'].browse(self._context.get('purchase_contract_id'))
    #         grn_ids = purchase_contract.mapped('request_payment_ids').filtered(
    #             lambda x: int(x.name) < int(self._context.get('sequence'))).mapped('grn_done_ids').ids
    #         domain += [('warehouse_id.code', 'in', ['FA', 'KTN-LT-N', 'KTN-AP-N']),
    #                    ('partner_id', '=', purchase_contract.partner_id.id), ('state', '=', 'done'),
    #                    ('picking_type_id.operation', '=', 'factory'),
    #                    ('product_id', '=', purchase_contract.product_id.id), ('id', 'not in', grn_ids)]
    #     if self._context.get('purchase_contract_id') and self._context.get('grn_ready'):
    #         purchase_contract = self.env['purchase.contract'].browse(self._context.get('purchase_contract_id'))
    #         domain += [('warehouse_id.code', 'in', ['FA', 'KTN-LT-N', 'KTN-AP-N']),
    #                    ('partner_id', '=', purchase_contract.partner_id.id),
    #                    ('state', 'not in', ['done', 'cancel', 'draft']), ('picking_type_id.operation', '=', 'factory'),
    #                    ('product_id', '=', purchase_contract.product_id.id)]
    #     if self._context.get('purchase_contract_id') and self._context.get('grn_fot_done'):
    #         purchase_contract = self.env['purchase.contract'].browse(self._context.get('purchase_contract_id'))
    #         domain += [('warehouse_id.code', 'in', ['FA']),
    #                    ('partner_id', '=', purchase_contract.partner_id.id),
    #                    ('state', '=', 'done'), ('picking_type_id.operation', '=', 'station'),
    #                    ('product_id', '=', purchase_contract.product_id.id)]
    #     return super(StockPicking, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)