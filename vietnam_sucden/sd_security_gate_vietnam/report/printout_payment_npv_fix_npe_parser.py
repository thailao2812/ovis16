# -*- encoding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.addons.report_aeroo.report_parser import Parser

import datetime
import time
import pytz
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

bank_name =False
partner = False
account_holder = False
acc_number = False

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

import datetime
from datetime import datetime
from pytz import timezone
import time
from datetime import datetime, timedelta

class Parser(models.AbstractModel):
    _name = 'report.printout_payment_npv_fixed_by_npe_report'
    _inherit = ['report.report_aeroo.abstract']
    _description = 'report.printout_payment_npv_fixed_by_npe_report'


    def _set_localcontext(self):
        localcontext = super(Parser, self)._set_localcontext()
        localcontext.update({
            'get_date': self.get_date,
            'manage_datetime': self.manage_datetime
        })
        return localcontext

    def get_date(self, date):
        if not date:
            date = datetime.now()
        date_user_tz = self.env['res.users']._convert_user_datetime(
            fields.Datetime.to_string(date))
        return date_user_tz.strftime('%d/%m/%Y')

    def manage_datetime(self, date):
        date_str = str(date + timedelta(hours=7))
        datetime_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S.%f')
        new_datetime_str = datetime_obj.strftime('%d-%m-%Y %H:%M:%S')
        return new_datetime_str