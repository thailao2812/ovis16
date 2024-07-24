# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import datetime, time, timedelta


class WizardRefuseRequest(models.TransientModel):
    _name = 'wizard.refuse.request'
    _description = "Wizard Refuse Request"

    reason = fields.Text(string="Reason")

    def action_refuse(self):
        request_payment = self.env['request.payment'].browse(self._context.get('active_ids', []))
        date_str = str(datetime.today() + timedelta(hours=7))
        datetime_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S.%f')
        new_datetime_str = datetime_obj.strftime('%d-%m-%Y %H:%M:%S')
        if request_payment:
            if request_payment.reason:
                request_payment.reason += '\n' + '(' + str(new_datetime_str) + ') ' + self.env.user.name + ': ' + self.reason
            else:
                request_payment.reason = '(' + str(new_datetime_str) + ') ' + self.env.user.name + ': ' + self.reason
        request_payment.state = 'draft'
