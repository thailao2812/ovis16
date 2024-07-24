# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"


class RejectReasonContract(models.TransientModel):
    _name = "reject.purchase.contract"

    reason = fields.Text(string='Reason Reject')
    state = fields.Selection([('draft', 'New'),
                              ('commercial', 'Commercial'),
                              ('accounting', 'Accounting'),
                              ('director', 'Director'),
                              ('approved', 'Approved'),
                              ('done', 'Done'),
                              ('cancel', 'Cancelled')],
                             string='Status',
                             readonly=True, copy=False, index=True, default='draft')

    @api.model
    def default_get(self, fields):
        res = {}
        active_id = self._context.get('active_id')
        if active_id:
            contract = self.env['purchase.contract'].browse(active_id)
            res = {'state': contract.state}
        return res

    def button_reject(self):
        active_id = self._context.get('active_id')
        contract = self.env['purchase.contract'].browse(active_id)
        if self.state == 'commercial':
            contract.reject_by_commercial = self.reason
            contract.button_cancel()
        if self.state == 'accounting':
            contract.reject_by_accounting = self.reason
            contract.button_cancel()
        if self.state == 'director':
            contract.reject_by_director = self.reason
            contract.button_cancel()