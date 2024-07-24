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
from num2words import num2words

import datetime
from datetime import datetime
from pytz import timezone
import time
from datetime import datetime, timedelta

class Parser(models.AbstractModel):
    _inherit = 'report.printout_payment_npv_report'
    

    def _set_localcontext(self):
        localcontext = super(Parser, self)._set_localcontext()
        localcontext.update({
            'get_paid_quantity': self.get_paid_quantity,
            'get_string_amount': self.get_string_amount,
            'get_liquidation': self.get_liquidation
        })
        return localcontext

    def get_paid_quantity(self, request):
        if request:
            seq = request.name
            if int(seq) > 1:
                purchase_contract = request.purchase_contract_id
                paid_quantity = sum(purchase_contract.request_payment_ids.filtered(lambda x: int(x.name) < int(seq)).mapped('payment_quantity'))
                return paid_quantity
            else:
                return 0

    def get_string_amount(self, o):
        amount_in_words = num2words(o.request_amount, lang='vi_VN')
        amount_in_words = amount_in_words[0].upper() + amount_in_words[1:]
        amount_in_words = amount_in_words + ' ' + 'đồng'
        return amount_in_words

    def get_liquidation(self, request):
        if request and int(request.name) == 1:
            return 10000000
        else:
            return 0