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




class Parser(models.AbstractModel):
    _name = 'report.report_commercial_invoice'
    _inherit = ['report.report_aeroo.abstract']
    _description = 'report.report_commercial_invoice'

    def _set_localcontext(self):
        localcontext = super(Parser, self)._set_localcontext()
        localcontext.update({
            'format_date_format': self.format_date_format,
            'calculate_net_qty': self.calculate_net_qty,
            'sum_total_net_qty': self.sum_total_net_qty,
            'sum_bags': self.sum_bags,
            'convert_s_name': self.convert_s_name,
            'sum_total_amount': self.sum_total_amount,
            'get_account_number': self.get_account_number,
            'get_nvs_name': self.get_nvs_name,
            'get_contract_price':self.get_contract_price
        })
        return localcontext
    
    def format_date_format(self, shipping):
        
        _date = date.today()
        # date_user_tz = self.env['res.users']._convert_user_datetime(
        #     fields.Datetime.to_string(_date))
        
        _date = _date.strftime('%Y-%m-%d')
        
            
        # shipping_date = self.env['res.users']._convert_user_datetime(
        #     fields.Datetime.to_string(shipping.date))
        date_shipment = False
        if shipping.shipment_date:
            date_shipment = shipping.shipment_date.strftime('%b-%d-%Y')
            # date_shipment = datetime.strptime(shipping.shipment_date, '%Y-%m-%d') 
        # else:
        #     date_shipment = _date
             
        return _date , date_shipment 
        
        
        _date = datetime.strptime(shipping.date, '%Y-%m-%d')
        date_shipment = datetime.strptime(shipping.shipment_date, '%Y-%m-%d')
        return datetime.strftime(_date, DATE_FORMAT), format_date(date_shipment, locale='en')

    def calculate_net_qty(self, shipping_line):
        if shipping_line:
            if shipping_line.diff_net > 0:
                amount = shipping_line.diff_net * shipping_line.price_unit
                return '{:,}'.format(int(shipping_line.diff_net)), '{:,}'.format(int(amount))
            else:
                amount = shipping_line.product_qty * shipping_line.price_unit
                return '{:,}'.format(int(shipping_line.product_qty)), '{:,}'.format(int(amount))
        return 0

    def sum_total_net_qty(self, shipping_line):
        total = 0
        if shipping_line:
            total += sum(i.diff_net for i in shipping_line.filtered(lambda x: x.diff_net > 0))
            total += sum(i.product_qty for i in shipping_line.filtered(lambda x: x.diff_net ==0))
        return '{:,}'.format(int(total))

    def sum_bags(self, shipping_line):
        total = 0
        if shipping_line:
            for i in shipping_line:
                packing = i.packing_id
                self.check_packing(packing, i)
                if (packing.tare_weight == 0 or packing.capacity == 0) and i.bags > 0:
                    total += i.bags
                if packing.tare_weight > 0 and packing.capacity > 0:
                    bags = round(i.product_qty / (packing.capacity + packing.tare_weight), 0)
                    total += bags
        return '{:,}'.format(int(total))

    def convert_s_name(self, shipping):
        if shipping:
            name = 'S' + shipping.contract_id.name
            return name

    def sum_total_amount(self, shipping):
        total = 0
        if shipping:
            for i in shipping.shipping_ids:
                total += int(self.calculate_net_qty(i)[1].replace(',', ''))
        return '{:,}'.format(int(total)), self.amount_to_text(total)

    def amount_to_text(self, nbr, lang='USD'):
        com = self.env['res.company'].search([], limit = 1)
        chuoi = com.with_context(lang='en_US').second_currency_id.amount_to_text(nbr)
        chuoi = chuoi[0].upper() + chuoi[1:]
        return chuoi
    

    def get_account_number(self):
        # bank = self.env['res.partner.bank'].browse( 8922)
        return '134 21322 845 205'

    def get_nvs_name(self, shipping):
        nvs = ''
        no_contract = ''
        if shipping:
            if shipping.contract_ids:
                nvs = '\n'.join(i.name for i in shipping.contract_ids)
            p_contract = '\n'.join(i.contract_p_id.name for i in shipping.contract_ids.filtered(
                lambda x: x.contract_p_id))
            value = []
            if len(shipping.contract_ids) <= 2:
                for i in shipping.contract_ids:
                    no = i.name.split('-')[1]
                    no = 'INV-' + str(datetime.today().year)[-2:] + '-' + no
                    value.append(no)
                no_contract = ', '.join(i for i in value)
            if len(shipping.contract_ids) >= 3:
                for i in shipping.contract_ids:
                    no = i.name.split('-')[1]
                    value.append(no)
                value = sorted(value, reverse=False)
                no_contract = 'INV-' + str(datetime.today().year)[-2:] + '-' + '/'.join(i for i in value)
            if shipping.reference:
                return nvs, shipping.reference, p_contract
            return nvs, no_contract, p_contract
    
    def get_contract_price(self, shipping):
        total_amount = 0
        total_qty = 0
        for x in shipping.contract_ids:
            for l in x.contract_line:
                total_amount += l.price_unit * l.product_qty
                total_qty += l.product_qty
        return total_qty and round((total_amount / total_qty), 4) or 0

    def check_packing(self, packing, shipping_line):
        if packing and shipping_line:
            if (packing.tare_weight == 0 or packing.capacity == 0) and shipping_line.bags == 0 and shipping_line.tare_weight == 0:
                raise UserError(_("You must input bags and tare weight > 0 in Product Lines"))
            if (packing.tare_weight == 0 or packing.capacity == 0) and (shipping_line.bags == 0 or shipping_line.tare_weight == 0):
                raise UserError(_("You must input bags and tare weight > 0 in Product Lines"))
    
    


