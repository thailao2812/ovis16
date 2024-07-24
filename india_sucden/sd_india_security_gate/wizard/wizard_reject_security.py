# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"


class RejectReasonSecurity(models.TransientModel):
    _name = "reject.delivery.registration"

    reason = fields.Text(string='Reason Reject')
    state = fields.Selection(
        [("draft", "Draft"), ("pur_approved", "Purchase"), ("qc_approved", "QC"), ('commercial', 'Commercial'),
         ("wh_approved", "WH"), ("approved", "Approved"), ("cancel", "Cancelled"), ("closed", "Closed"),
         ("reject", "Reject")], string="Status",
        readonly=True, copy=False, index=True, default='draft')

    @api.model
    def default_get(self, fields):
        res = {}
        active_id = self._context.get('active_id')
        if active_id:
            delivery_registration = self.env['ned.security.gate.queue'].browse(active_id)
            res = {'state': delivery_registration.state}
        return res

    def button_reject(self):
        active_id = self._context.get('active_id')
        delivery_registration = self.env['ned.security.gate.queue'].browse(active_id)
        if self.state == 'pur_approved':
            delivery_registration.reject_purchase = self.reason
            delivery_registration.button_reject()
        if self.state == 'qc_approved':
            delivery_registration.reject_qc = self.reason
            delivery_registration.button_reject()
        if self.state == 'wh_approved':
            delivery_registration.reject_warehouse = self.reason
            delivery_registration.button_reject()
        if self.state == 'commercial':
            delivery_registration.reject_commercial = self.reason
            delivery_registration.button_reject()