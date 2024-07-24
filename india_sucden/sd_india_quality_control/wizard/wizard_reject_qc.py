# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"


class RejectReasonQC(models.TransientModel):
    _name = "reject.qc"

    reason = fields.Text(string='Reason Reject')

    def button_reject(self):
        active_id = self._context.get('active_id')
        qc = self.env['stock.picking'].browse(active_id)
        qc.reject_in_qc = self.reason
        qc.btt_reject()