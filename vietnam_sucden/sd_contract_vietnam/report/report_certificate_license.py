# -*- encoding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.addons.report_aeroo.report_parser import Parser
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
from num2words import num2words

from pytz import timezone
from datetime import datetime, timedelta


class Parser(models.AbstractModel):
    _name = 'report.report_certificate_license'
    _inherit = ['report.report_aeroo.abstract']
    _description = 'report.report_certificate_license'

    def _set_localcontext(self):
        localcontext = super(Parser, self)._set_localcontext()
        localcontext.update({
            'get_date': self.get_date,
            'get_datetime': self.get_datetime
        })
        return localcontext


    def get_date(self, date):
        if not date:
            date = datetime.now()
        date_user_tz = self.env['res.users']._convert_user_datetime(
            fields.Datetime.to_string(date))
        date = date_user_tz.strftime('%d/%m/%Y')
        return date

    def get_datetime(self, date):
        if not date:
            date = datetime.now()

        date_user_tz = self.env['res.users']._convert_user_datetime(
            fields.Datetime.to_string(date))
        # date = str(res_user._convert_user_datetime(self.cr,self.uid,date))
        # date = datetime.strptime(date[0:19], DATETIME_FORMAT)
        return date_user_tz.strftime('%d/%m/%Y %H:%M:%S')