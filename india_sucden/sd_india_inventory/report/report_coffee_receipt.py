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
    _name = 'report.grn_receipt_report'
    _inherit = ['report.report_aeroo.abstract']
    _description = 'report.grn_receipt_report'


    def _set_localcontext(self):
        localcontext = super(Parser, self)._set_localcontext()
        localcontext.update({
            'get_string_selection': self.get_string_selection,
            'get_all_contract': self.get_all_contract,
            'get_date': self.get_date,
            'get_data_dr': self.get_data_dr,
            'get_data_picking': self.get_data_picking,
            'convert_to_date': self.convert_to_date,
            'get_contract_convert': self.get_contract_convert,
            'get_contract_advance': self.get_contract_advance
        })
        return localcontext

    def get_date(self, date):
        if date:
            convert_str = date.strftime(DATETIME_FORMAT)
            return_date = str((datetime.strptime(convert_str, DATETIME_FORMAT) + timedelta(hours=5, minutes=30)).date())
            date_convert = datetime.strptime(return_date, '%Y-%m-%d')
            date_convert = date_convert.strftime('%d-%m-%Y')
            return date_convert

    def convert_to_date(self, date):
        if not date:
            date = datetime.now()
        date_user_tz = self.env['res.users']._convert_user_datetime(
            fields.Datetime.to_string(date))
        date = date_user_tz.strftime('%d/%m/%Y')
        return date

    def get_string_selection(self, picking):
        if picking:
            if picking.type_contract == 'cr':
                return 'CR'
            elif picking.type_contract == 'cs':
                return 'CS'
            elif picking.type_contract == 'ra_cr':
                return 'RA-CR'
            elif picking.type_contract == 'ra_cs':
                return 'RA-CS'
            elif picking.type_contract == 'sdv_cr':
                return 'SDV-CR'
            elif picking.type_contract == 'sdv_cs':
                return 'SDV-CS'
            elif picking.type_contract == 'eudr_cr':
                return 'EUDR-CR'
            elif picking.type_contract == 'eudr_cs':
                return 'EUDR-CS'
        return ''

    def get_all_contract(self, picking):
        if picking:
            stock_allocation = self.env['stock.allocation'].search([
                ('picking_id', '=', picking.id),
            ])
            return ', '.join(i.contract_id.name for i in stock_allocation)
        return ''

    def get_data_dr(self, picking):
        if picking:
            origin = picking.origin
            delivery_registration = self.env['ned.security.gate.queue'].search([
                ('name', '=', origin)
            ])
            if delivery_registration:
                name = delivery_registration.name
                bags = delivery_registration.estimated_bags
                qty = delivery_registration.approx_quantity
                truck = delivery_registration.license_plate
                supplier = delivery_registration.supplier_id.name
                estate_name = delivery_registration.estate_name
                created_by = delivery_registration.security_id.name
                date = self.get_date(delivery_registration.arrivial_time)
                return name, date, truck, bags, qty, supplier, estate_name, created_by
            return '', '', '', '', '', '', '', ''
        return '', '', '', '', '', '', '', ''

    def get_data_picking(self, picking):
        if picking:
            first_weight = picking.first_weight
            second_weight = picking.second_weight
            gross_weight = picking.total_init_qty
            tare_weight = picking.tare_weight
            net_weight = picking.total_qty
            bag = picking.total_bag
            warehouse = picking.warehouse_id.name
            if picking.lot_id:
                zone = picking.lot_id.zone_id.name
                stack = picking.lot_id.name
            else:
                zone = ''
                stack = ''
            packing = picking.packing_id.name
            return ('{:,}'.format(int(first_weight)), '{:,}'.format(int(second_weight)), '{:,}'.format(int(gross_weight)),
                    '{:,}'.format(int(tare_weight)), '{:,}'.format(int(net_weight)), '{:,}'.format(int(bag)), warehouse, zone, stack, packing)
        return '', '', '', '', '', '', '', '', '', ''

    def get_contract_advance(self, picking):
        if picking:
            contract_cs = self.env['stock.allocation'].search([
                ('picking_id', '=', picking.id),
                ('contract_id.type', '=', 'consign'),
                ('contract_id.npe_ids', '!=', False),
                ('contract_id.request_payment_ids', '!=', False)
            ]).mapped('contract_id')
            contract_cr_removed = []
            for con in contract_cs:
                for line in con.npe_ids:
                    if line.contract_id.state == 'cancel':
                        contract_cr_removed.append(line.contract_id.id)
            value = []
            for con in contract_cs:
                balance = con.request_payment_ids[0].request_amount
                for line in con.npe_ids:
                    if line.contract_id.id in contract_cr_removed:
                        continue
                    balance -= sum(line.contract_id.pay_allocation_ids.mapped('allocation_amount'))
                    value.append({
                        'cs_no': con.name,
                        'cs_date': self.convert_to_date(con.request_payment_ids[0].date),
                        'price_kg': '{:,.2f}'.format(int(con.request_payment_ids[0].price)),
                        'amount': '{:,}'.format(int(con.request_payment_ids[0].request_amount)),
                        'balance': '{:,}'.format(int(balance)),
                        'cr_no': line.contract_id.name,
                        'cr_date': self.convert_to_date(line.contract_id.date_order),
                        'allocation': '{:,}'.format(int(sum(line.contract_id.pay_allocation_ids.mapped('allocation_amount')))),
                        'interest': '{:,}'.format(int(sum(line.contract_id.pay_allocation_ids.mapped('total_interest_pay')))),
                    })
            return value
        return []


    def get_contract_convert(self, picking):
        if picking:
            contract_cs = self.env['stock.allocation'].search([
                ('picking_id', '=', picking.id),
                ('contract_id.type', '=', 'consign'),
                ('contract_id.npe_ids', '!=', False)
            ]).mapped('contract_id')
            contract_cr_removed = []
            for con in contract_cs:
                for line in con.npe_ids:
                    if line.contract_id.state == 'cancel':
                        contract_cr_removed.append(line.contract_id.id)
            value = []
            for con in contract_cs:
                balance_qty = con.total_qty
                for line in con.npe_ids:
                    if line.contract_id.id in contract_cr_removed:
                        continue
                    balance_qty -= line.contract_id.gross_qty
                    value.append({
                        'cs_no': con.name,
                        'cs_date': self.convert_to_date(con.date_order),
                        'cs_qty': '{:,}'.format(int(con.total_qty)),
                        'balance_qty': '{:,}'.format(int(balance_qty)),
                        'cr_no': line.contract_id.name,
                        'cr_date': self.convert_to_date(line.contract_id.date_order),
                        'cr_qty': '{:,}'.format(int(line.contract_id.gross_qty)),
                        'cr_price': '{:,.2f}'.format(int(line.contract_id.relation_price_unit)),
                        'rate_bag': '{:,.2f}'.format(int(line.contract_id.relation_price_unit * 50)),
                    })
            return value
        else:
            return []

