# -*- encoding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.addons.report_aeroo.report_parser import Parser

import datetime
import time
import pytz
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

bank_name = False
partner = False
account_holder = False
acc_number = False

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

import datetime
from datetime import datetime
from pytz import timezone
import time


class Parser(models.AbstractModel):
    _name = 'report.report_ptbf_minutes_of_closing_price'
    _inherit = ['report.report_aeroo.abstract']
    _description = 'report.report_ptbf_minutes_of_closing_price'

    def _set_localcontext(self):
        localcontext = super(Parser, self)._set_localcontext()
        localcontext.update({
            'get_date': self.get_date,
            'get_no_of_contract': self.get_no_of_contract,
            'get_minutes_of_fixation': self.get_minutes_of_fixation
        })
        return localcontext

    def get_minutes_of_fixation(self, request):
        if request:
            ptbf_fix_price_no = request.price_tobe_fix.no
            search_other_request = self.env['request.payment'].search([
                ('type', '=', 'ptbf'),
                ('type_of_ptbf_payment', '=', 'fixation'),
                ('price_tobe_fix', '=', request.price_tobe_fix.id),
                ('create_date', '<', request.create_date),
            ])
            return str(ptbf_fix_price_no) + '/' + str(len(search_other_request) + 1)

    def get_date(self, date):
        if not date:
            date = datetime.now()
        date_user_tz = self.env['res.users']._convert_user_datetime(
            fields.Datetime.to_string(date))
        date = date_user_tz.strftime('%d/%m/%Y')
        return date

    def get_no_of_contract(self, history):
        if history:
            history_line = self.env['history.rate'].search([
                ('ptbf_id', '=', history.ptbf_id.id),
                ('id', '!=', history.id),
                ('date_receive', '<=', history.date_receive),
                ('history_id', '=', history.history_id.id)
            ])
            if history_line:
                return str(history.history_id.no) + '/' + str(len(history_line) + 1)
            else:
                return str(history.history_id.no) + '/' + '1'
