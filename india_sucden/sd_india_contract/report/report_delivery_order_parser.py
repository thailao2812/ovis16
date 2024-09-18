# -*- encoding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError
from datetime import datetime
from datetime import date

import time
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%d-%m-%Y"
# -*- encoding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.addons.report_aeroo.report_parser import Parser
from babel.dates import format_date, format_datetime, format_time
import math




class Parser(models.AbstractModel):
    _name = 'report.report_delivery_order_india'
    _inherit = ['report.report_aeroo.abstract']
    _description = 'report.report_delivery_order_india'

    def _set_localcontext(self):
        localcontext = super(Parser, self)._set_localcontext()

        localcontext.update({
            'get_date': self.get_date,
            'get_allocate': self.get_allocate,
            'get_total': self.get_total,
            'get_price': self.get_price,
            'get_address': self.get_address,
            'get_certificate': self.get_certificate,
            'get_symbol_currency': self.get_symbol_currency,
            'get_stack_packing': self.get_stack_packing
        })
        return localcontext

    def get_date(self, date):
        if not date:
            return True
        date_user_tz = self.env['res.users']._convert_user_datetime(
            fields.Datetime.to_string(date))

        return date_user_tz.strftime('%d/%m/%Y')

    def get_allocate(self, delivery_order):
        if delivery_order:
            stock_allocation = self.env['lot.stack.allocation'].search([
                ('delivery_id', '=', delivery_order.id)
            ])
            return stock_allocation
        return True

    def get_total(self, delivery_order):
        if delivery_order:
            stock_allocation = self.env['lot.stack.allocation'].search([
                ('delivery_id', '=', delivery_order.id)
            ])
            total_qty = sum(stock_allocation.mapped('quantity'))
            total_amount = 0
            for i in stock_allocation:
                total_amount += i.quantity * (self.get_price(delivery_order) / 1000)

            return '{:,}'.format(int(total_qty)), "{:,.2f}".format(self.custom_round(total_amount))

    def get_stack_packing(self, delivery_order):
        stock_allocation = self.get_allocate(delivery_order)
        if stock_allocation:
            return "/".join(i.stack_id.name for i in stock_allocation), "/".join(i.packing_id.name for i in stock_allocation), sum(stock_allocation.mapped('no_of_bag'))
        else:
            return '', '', 0

    def custom_round(self, number: float) -> int:
        if number - round(number) == 0.5:
            return math.ceil(number)
        else:
            return round(number)

    def get_price(self, deliver_order):
        if deliver_order:
            return round((deliver_order.contract_id.amount_total / deliver_order.contract_id.total_qty) * 1000, 3)

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

    def get_certificate(self, delivery_order):
        if delivery_order:
            scontract_id = delivery_order.shipping_id.contract_id
            certificate = scontract_id.mapped('certificated_ids')
            if certificate:
                return '- ' + certificate[0].code
            else:
                return True

    def get_symbol_currency(self, delivery_order):
        if delivery_order:
            currency = delivery_order.currency_id
            return currency.symbol

