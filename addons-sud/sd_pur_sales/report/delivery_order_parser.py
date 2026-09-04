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
    _name = 'report.report_delivery_orders'
    _inherit = ['report.report_aeroo.abstract']
    _description = 'report.report_delivery_orders'
    
    def _set_localcontext(self):
        localcontext = super(Parser, self)._set_localcontext()
        
        global bank_name
        global partner
        global account_holder
        global acc_number
        
        bank_name =False
        partner = False
        account_holder = False
        acc_number = False
        localcontext.update({
            'get_string_amount':self.get_string_amount,
            'get_date':self.get_date,
            'get_capacity':self.get_capacity,
            'get_buyer':self.get_buyer,
            'get_recipient':self.get_recipient,
            'get_delivery_place':self.get_delivery_place
        })
        return localcontext
    
    def get_string_amount(self, qty):
        com = self.env['res.company'].search([], limit = 1)
        chuoi = com.with_context(lang='vi_VN').second_currency_id.amount_to_text(qty)   
        chuoi = chuoi.replace(u'đồng',u'kilogram')
        chuoi = chuoi[0].upper() + chuoi[1:]
        return chuoi
    
    def get_delivery_place(self,o):
        if o.delivery_place_id:
            return o.delivery_place_id.name or ''
        if o.contract_id.shipping_id:
            return o.contract_id.shipping_id.delivery_place_id and o.contract_id.shipping_id.delivery_place_id.name or ''
        else:
            return o.warehouse_id.name
    
    def get_recipient(self,o):
        if o.type == 'Sale':
            return u'Công ty TNHH Sucden Coffee Việt Nam (Trạm TP.HCM)'
        else:
            return u'Công ty TNHH Sucden Coffee Việt Nam'
        
    def get_buyer(self,o):
        if o.type == 'Sale':
            if 'svns' in o.contract_id.name.lower():
                return u'SUCDEN COFFEE NETHERLANDS BV'
            else:
                return '            '
        else:
            return '            '
    
    def get_date(self, o):
        date = o.date
        if not date:
            date = datetime.now()
        date_user_tz = self.env['res.users']._convert_user_datetime(
            fields.Datetime.to_string(date))
        
        return date_user_tz.strftime('%d/%m/%Y')
    
    def get_capacity(self,o):
        if o.delivery_order_ids[0].bags_input > 0:
            return o.delivery_order_ids[0].bags_input
        elif o.delivery_order_ids[0].packing_id and o.delivery_order_ids[0].packing_id.capacity:
            return round(o.total_qty / o.delivery_order_ids[0].packing_id.capacity,0)
        else:
            return o.total_qty
    


