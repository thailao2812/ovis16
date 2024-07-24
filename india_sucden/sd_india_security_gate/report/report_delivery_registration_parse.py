from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.addons.report_aeroo.report_parser import Parser
from num2words import num2words
from currency2text import supported_language, currency_to_text
from datetime import datetime, timedelta
import time
import pytz
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

bank_name = False
partner = False
account_holder = False
acc_number = False
import math
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class Parser(models.AbstractModel):
    _name = 'report.delivery_registration_india'
    _inherit = ['report.report_aeroo.abstract']
    _description = 'report.delivery_registration_india'

    def _set_localcontext(self):
        localcontext = super(Parser, self)._set_localcontext()
        localcontext.update({
            'get_grn': self.get_grn,
            'get_type_contract': self.get_type_contract,
            'get_state': self.get_state,
            'get_date_time': self.get_date_time
        })
        return localcontext

    def get_date_time(self, dr):
        if dr:
            date_dr = str(dr.arrivial_time)
            date_string_without_microseconds = date_dr.split('.')[0]
            datetime_object = datetime.strptime(date_string_without_microseconds, DATETIME_FORMAT) + timedelta(hours=5, minutes=30)
            formatted_date_string = datetime_object.strftime('%d-%m-%Y %H:%M:%S')
            return formatted_date_string

    def get_grn(self, dr):
        if dr:
            grn = self.env['stock.picking'].search([
                ('security_gate_id', '=', dr.id)
            ])
            if grn:
                return grn.name
            else:
                return ''

    def get_type_contract(self, dr):
        if dr:
            if dr.type_contract == 'cr':
                return 'Regular Contract'
            else:
                return 'Consignment Contract'

    def get_state(self, dr):
        if dr:
            selected_string = dict(dr._fields['state'].selection).get(dr.state)
            return selected_string