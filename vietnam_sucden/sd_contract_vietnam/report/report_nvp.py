# -*- encoding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.addons.report_aeroo.report_parser import Parser
from datetime import datetime, timedelta, date

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
    _inherit = 'report.nvp_report'

    def _set_localcontext(self):
        localcontext = super(Parser, self)._set_localcontext()

        localcontext.update({
            'get_license_2nd': self.get_license_2nd
        })
        return localcontext


    def get_license_2nd(self, purchase):
        if purchase:
            if purchase.license_2nd_id:
                return '(' + purchase.license_2nd_id.name + ')'
            else:
                return ''
        else:
            return ''