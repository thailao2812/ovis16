from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.addons.report_aeroo.report_parser import Parser
from num2words import num2words
from currency2text import supported_language, currency_to_text
from datetime import datetime, date, timedelta
import time
import pytz
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

bank_name = False
partner = False
account_holder = False
acc_number = False

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class Parser(models.AbstractModel):
    _name = 'report.purchase_contract_return_goods'
    _inherit = ['report.report_aeroo.abstract']
    _description = 'report.purchase_contract_return_goods'

    def _set_localcontext(self):
        localcontext = super(Parser, self)._set_localcontext()
        localcontext.update({
            'get_address': self.get_address,
            'get_date': self.get_date,
            'get_document_return': self.get_document_return,
            'get_sum_return_bag': self.get_sum_return_bag,
            'get_sum_return_quantity': self.get_sum_return_quantity,
            'get_reason_return': self.get_reason_return,
            'get_data_contract': self.get_data_contract,
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

    def get_document_return(self, purchase_contract):
        if purchase_contract:
            if purchase_contract.picking_return_ids:
                document = ", ".join(i.name for i in purchase_contract.picking_return_ids.filtered(lambda x: x.state == 'done'))
                return document
            return ''

    def get_sum_return_bag(self, purchase_contract):
        if purchase_contract:
            if purchase_contract.picking_return_ids:
                bag = sum(purchase_contract.picking_return_ids.filtered(lambda x: x.state == 'done').mapped('total_bag'))
                return int(bag)
            return 0

    def get_sum_return_quantity(self, purchase_contract):
        if purchase_contract:
            if purchase_contract.picking_return_ids:
                quantity = sum(purchase_contract.picking_return_ids.filtered(lambda x: x.state == 'done').mapped('total_qty'))
                return int(quantity)
            return 0

    def get_reason_return(self, picking):
        if picking:
            return_request = self.env['return.goods.cs.contract'].search([
                ('picking_id', '=', picking.id),
            ])
            if return_request:
                return return_request.reason

    def get_data_contract(self, picking):
        if picking:
            contract = self.env['purchase.contract'].search([
                ('picking_return_ids', 'in', picking.ids),
            ])
            if contract:
                return contract.name, self.get_date(contract.date_order), contract.license_id.name if contract.license_id else '', '{:,}'.format(int(contract.total_qty)), '{:,}'.format(int(contract.number_of_bags))
