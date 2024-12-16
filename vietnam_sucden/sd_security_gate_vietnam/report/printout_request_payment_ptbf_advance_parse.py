# -*- encoding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.addons.report_aeroo.report_parser import Parser

import datetime
import time
import pytz
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from num2words import num2words

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

from datetime import datetime, timedelta

class Parser(models.AbstractModel):
    _name = 'report.printout_request_payment_ptbf_advance_report'
    _inherit = ['report.report_aeroo.abstract']
    _description = 'report.printout_request_payment_ptbf_advance_report'

    def _set_localcontext(self):
        localcontext = super(Parser, self)._set_localcontext()
        localcontext.update({
            'get_date': self.get_date,
        })
        return localcontext


    def get_date(self, date):
        if not date:
            date = datetime.now()
        date_user_tz = self.env['res.users']._convert_user_datetime(
            fields.Datetime.to_string(date))
        return date_user_tz.strftime('%d/%m/%Y')