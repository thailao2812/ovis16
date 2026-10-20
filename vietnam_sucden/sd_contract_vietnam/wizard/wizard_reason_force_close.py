# -*- encoding: utf-8 -*-
from odoo import fields, models, api, _
import base64
import xlrd
import pytz
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class WizardForceCloseNPE(models.TransientModel):
    _name = 'force.close.npe'
    _description = 'Force Close NPE'

    reason = fields.Text(string='Reason', required=True)

    def action_confirm(self):
        purchase_contract = self.env['purchase.contract'].browse(self._context.get('res_id'))
        purchase_contract.write({'state': 'done'})
        vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        current_datetime = datetime.now(vietnam_tz).strftime('%d-%m-%Y %H:%M:%S')
        purchase_contract.message_post(
            body=_("This Contract has been closed because of: %s by %s at %s") % (self.reason, self.env.user.name, current_datetime))