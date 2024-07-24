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
    _name = 'report.contract_regular_detail_india_report'
    _inherit = ['report.report_aeroo.abstract']
    _description = 'report.contract_regular_detail_india_report'


    def _set_localcontext(self):
        localcontext = super(Parser, self)._set_localcontext()
        localcontext.update({
            'get_date': self.get_date,
            'currency_to_text_india': self.currency_to_text_india,
            'get_contract': self.get_contract,
            'get_address': self.get_address,
            "get_total_amount": self.get_total_amount,
            'get_data_amount': self.get_data_amount
        })
        return localcontext

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

    def get_date(self, date):
        if date:
            convert_str = date.strftime(DATETIME_FORMAT)
            return_date = str((datetime.strptime(convert_str, DATETIME_FORMAT) + timedelta(hours=5, minutes=30)).date())
            date_convert = datetime.strptime(return_date, '%Y-%m-%d')
            date_convert = date_convert.strftime('%d-%m-%Y')
            return date_convert

    def get_contract(self, contract):
        if contract:
            return contract

    def get_total_amount(self, contract):
        contract = self.get_contract(contract=contract)
        if contract:
            total_amount = 0
            total_tax = sum(contract.mapped('amount_tax'))
            grand_total = 0
            for line in contract:
                grand_total += (line.relation_price_unit + line.premium) * line.total_qty
                total_amount += (line.relation_price_unit + line.premium) * line.total_qty
            grand_total = self.custom_round(grand_total)
            total_amount = self.custom_round(total_amount)
            return total_amount, total_tax, grand_total
        else:
            return 0

    def currency_to_text_india(self, total):
        total = "{:.2f}".format(total)
        total = total.replace(',', '')
        total = float(total)
        string = num2words(float(total), lang="en_IN")
        string = string.replace(',', '')
        split_str = string.split(' ')
        arr = []
        for i in split_str:
            str_after = i.capitalize()
            arr.append(str_after)
        last_str = ' '.join(i for i in arr)
        last_str = last_str + ' Only'
        return last_str

    def custom_round(self, number: float) -> int:
        if number - round(number) == 0.5:
            return math.ceil(number)
        else:
            return round(number)

    def get_data_amount(self, contract):
        if contract:
            amount = (contract.relation_price_unit + contract.premium) * contract.total_qty
            amount = self.custom_round(amount)
            grand_total = (contract.relation_price_unit + contract.premium) * contract.total_qty + contract.amount_tax
            grand_total = self.custom_round(grand_total)
            return amount, grand_total