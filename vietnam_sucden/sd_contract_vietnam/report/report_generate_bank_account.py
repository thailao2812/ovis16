# -*- encoding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.addons.report_aeroo.report_parser import Parser
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
from num2words import num2words

from pytz import timezone
from datetime import datetime, timedelta


class Parser(models.AbstractModel):
    _name = 'report.report_generate_bank_account'
    _inherit = ['report.report_aeroo.abstract']
    _description = 'report.report_generate_bank_account'

    def _set_localcontext(self):
        localcontext = super(Parser, self)._set_localcontext()
        localcontext.update({
        })
        return localcontext