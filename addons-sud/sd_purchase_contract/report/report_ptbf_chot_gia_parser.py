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



class Parser(models.AbstractModel):
    _name = 'report.report_ptbf_chot_gia'
    _inherit = ['report.report_aeroo.abstract']
    _description = 'report.report_ptbf_chot_gia'
    
    def _set_localcontext(self):
        localcontext = super(Parser, self)._set_localcontext()
        localcontext.update({
            'get_date':self.get_date,
            'get_no_of_contract': self.get_no_of_contract
        })
        return localcontext
    
    def get_date(self, date):
        if not date:
            date = datetime.now()
        date_user_tz = self.env['res.users']._convert_user_datetime(
            fields.Datetime.to_string(date))
        date = date_user_tz.strftime('%d/%m/%Y')

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
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
