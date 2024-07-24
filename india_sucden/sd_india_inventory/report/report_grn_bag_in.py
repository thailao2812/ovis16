from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.addons.report_aeroo.report_parser import Parser
from num2words import num2words
from currency2text import supported_language, currency_to_text
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
from datetime import datetime, timedelta


class Parser(models.AbstractModel):
    _name = 'report.grn_india_bag_in_report'
    _inherit = ['report.report_aeroo.abstract']
    _description = 'report.grn_india_bag_in_report'

    def _set_localcontext(self):
        localcontext = super(Parser, self)._set_localcontext()
        localcontext.update({
            'get_date': self.get_date,
            'get_address': self.get_address,
            'get_info_partner': self.get_info_partner
        })
        return localcontext

    def get_date(self, date):
        if date:
            convert_str = date.strftime(DATETIME_FORMAT)
            return_date = str((datetime.strptime(convert_str, DATETIME_FORMAT) + timedelta(hours=5, minutes=30)).date())
            date_convert = datetime.strptime(return_date, '%Y-%m-%d')
            date_convert = date_convert.strftime('%d-%m-%Y')
            return date_convert

    def get_address(self, partner_id):
        street = ''
        if partner_id:
            street = ', '.join([x for x in (partner_id.street, partner_id.street2) if x])
            if partner_id.district_id:
                street += ' ' + partner_id.district_id.name + ' '
            if partner_id.city:
                street += partner_id.city + ' '
            if partner_id.state_id:
                street += partner_id.state_id.name
        return street

    def get_info_partner(self, partner):
        if partner:
            info = '/ '.join([x for x in (partner.phone, partner.mobile) if x])
            return info
        else:
            return ''