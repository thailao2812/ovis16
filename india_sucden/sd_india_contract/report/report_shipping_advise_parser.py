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

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class Parser(models.AbstractModel):
    _name = 'report.report_shipping_advise_india'
    _inherit = ['report.report_aeroo.abstract']
    _description = 'report.report_shipping_advise_india'

    def _set_localcontext(self):
        localcontext = super(Parser, self)._set_localcontext()
        localcontext.update({
            'compute_address': self.compute_address,
            'get_no_of_bag': self.get_no_of_bag,
            'get_date': self.get_date,
            'get_container_status': self.get_container_status,
            'get_number_of_do': self.get_number_of_do,
            'get_total_qty_mt': self.get_total_qty_mt,
            'get_total_container': self.get_total_container
        })
        return localcontext

    def compute_address(self, partner):
        if partner:
            address = ', '.join([x for x in (partner.street, partner.street2) if x])
            if partner.district_id:
                address += ' ' + partner.district_id.name + ' '
            if partner.city:
                address += partner.city + ' '
            if partner.state_id:
                address += partner.state_id.name
            return address

    def get_date(self, date):
        if not date:
            today = datetime.today().date()
            convert_str = today.strftime(DATETIME_FORMAT)
            return_date = str((datetime.strptime(convert_str, DATETIME_FORMAT) + timedelta(hours=5, minutes=30)).date())
            date_convert = datetime.strptime(return_date, '%Y-%m-%d')
            date_convert = date_convert.strftime('%d-%m-%Y')
            return date_convert
        if date:
            convert_str = date.strftime(DATETIME_FORMAT)
            return_date = str((datetime.strptime(convert_str, DATETIME_FORMAT) + timedelta(hours=5, minutes=30)).date())
            date_convert = datetime.strptime(return_date, '%Y-%m-%d')
            date_convert = date_convert.strftime('%d-%m-%Y')
            return date_convert

    def get_no_of_bag(self, post_shipment):
        if post_shipment:
            bags = sum(post_shipment.post_line.mapped('bags'))
            packing = ''
            if post_shipment.packing_id:
                packing = post_shipment.packing_id.name
            return str(bags) + ' ' + packing

    def get_container_status(self, post_shipment):
        if post_shipment:
            shipping_line = ''
            container_status = ''
            if post_shipment.shipping_id:
                if post_shipment.shipping_id.shipping_line_id:
                    shipping_line = post_shipment.shipping_id.shipping_line_id.name
                if post_shipment.shipping_id.container_status:
                    if post_shipment.shipping_id.container_status == 'fcl/fcl':
                        container_status = 'FCL/FCL'
                    if post_shipment.shipping_id.container_status == 'lcl/fcl':
                        container_status = 'LCL/FCL'
                    if post_shipment.shipping_id.container_status == 'lcl/lcl':
                        container_status = 'LCL/LCL'
            if shipping_line and not container_status:
                return shipping_line
            if not shipping_line and container_status:
                return container_status
            if not shipping_line and not container_status:
                return True
            if shipping_line and container_status:
                return str(shipping_line) + '-' + str(container_status)

    def get_number_of_do(self, post_shipment):
        if post_shipment:
            return len(post_shipment.post_line.mapped('do_id'))

    def get_total_qty_mt(self, post_shipment):
        if post_shipment:
            do_ids = post_shipment.post_line.mapped('do_id')
            total_do = sum(do_ids.mapped('delivery_order_ids.product_qty'))
            return '{:,.3f}'.format(total_do/1000)

    def get_total_container(self, post_shipment):
        if post_shipment:
            if any(post_shipment.post_line.mapped('cont_no')):
                container = ', '.join(i.cont_no for i in post_shipment.post_line)
                return container
            else:
                return ''
