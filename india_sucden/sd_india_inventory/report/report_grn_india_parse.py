# -*- encoding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.addons.report_aeroo.report_parser import Parser
from num2words import num2words
from currency2text import supported_language, currency_to_text
import datetime
import time
import pytz
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

bank_name =False
partner = False
account_holder = False
acc_number = False
import math
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

import datetime
from datetime import datetime
from pytz import timezone
import time
from datetime import datetime, timedelta

class Parser(models.AbstractModel):
    _name = 'report.grn_india_report'
    _inherit = ['report.report_aeroo.abstract']
    _description = 'report.grn_india_report'

    def _set_localcontext(self):
        localcontext = super(Parser, self)._set_localcontext()
        localcontext.update({
            'get_address': self.get_address,
            'get_dr': self.get_dr,
            'get_date': self.get_date,
            'get_contract': self.get_contract,
            'currency_to_text_india': self.currency_to_text_india,
            'get_total_amount': self.get_total_amount,
            'get_data_amount': self.get_data_amount,
            'get_allocate_qty': self.get_allocate_qty,
            'get_total_allocate_qty': self.get_total_allocate_qty
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

    def get_dr(self, picking):
        if picking:
            doc = picking.origin.strip()
            delivery_registration = self.env['ned.security.gate.queue'].search([
                ('name', '=', doc)
            ])
            if delivery_registration:
                convert_str = delivery_registration.arrivial_time.strftime(DATETIME_FORMAT)
                date = str((datetime.strptime(convert_str, DATETIME_FORMAT) + timedelta(hours=5, minutes=30)).date())
                date_convert = datetime.strptime(date, '%Y-%m-%d')
                date_convert = date_convert.strftime('%d-%m-%Y')
                return delivery_registration.name, date_convert

    def get_date(self, date):
        if date:
            convert_str = date.strftime(DATETIME_FORMAT)
            return_date = str((datetime.strptime(convert_str, DATETIME_FORMAT) + timedelta(hours=5, minutes=30)).date())
            date_convert = datetime.strptime(return_date, '%Y-%m-%d')
            date_convert = date_convert.strftime('%d-%m-%Y')
            return date_convert

    def get_contract(self, picking):
        if picking:
            stock_allocation = self.env['stock.allocation'].search([
                ('picking_id', '=', picking.id),
                ('state', '=', 'approved'),
                ('contract_id.type', '=', 'purchase')
            ])
            if stock_allocation:
                return stock_allocation.mapped('contract_id')
            else:
                return False

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

    def get_total_amount(self, picking):
        contract = self.get_contract(picking=picking)
        if contract:
            total_amount = 0
            total_tax = sum(contract.mapped('amount_tax'))
            grand_total = 0
            for line in contract:
                grand_total += (line.relation_price_unit + line.premium) * self.get_allocate_qty(picking, line)
                total_amount += (line.relation_price_unit + line.premium) * self.get_allocate_qty(picking, line)
            grand_total = self.custom_round(grand_total)
            total_amount = self.custom_round(total_amount)
            return total_amount, total_tax, grand_total
        else:
            return 0

    def custom_round(self, number: float) -> int:
        if number - round(number) == 0.5:
            return math.ceil(number)
        else:
            return round(number)

    def get_data_amount(self, contract, picking):
        if contract:
            amount = (contract.relation_price_unit + contract.premium) * self.get_allocate_qty(picking, contract)
            amount = self.custom_round(amount)
            return amount

    def get_allocate_qty(self, picking, contract):
        if picking and contract:
            stock_allocation = self.env['stock.allocation'].search([
                ('picking_id', '=', picking.id),
                ('state', '=', 'approved'),
                ('contract_id', '=', contract.id)
            ])
            if stock_allocation:
                return stock_allocation.qty_allocation

    def get_total_allocate_qty(self, picking):
        if picking:
            stock_allocation = self.env['stock.allocation'].search([
                ('picking_id', '=', picking.id),
                ('state', '=', 'approved'),
                ('contract_id.type', '=', 'purchase')
            ])
            return sum(stock_allocation.mapped('qty_allocation'))


