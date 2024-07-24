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
    _name = 'report.trucking_list_report'
    _inherit = ['report.report_aeroo.abstract']
    _description = 'report.trucking_list_report'
    
    global bank_name
    global partner
    global account_holder
    global acc_number
    
    
    bank_name =False
    partner = False
    account_holder = False
    acc_number = False

    def _set_localcontext(self):
        localcontext = super(Parser, self)._set_localcontext()
        localcontext.update({
            'get_date':self.get_date,
            'get_header':self.get_header,
            'get_capacity':self.get_capacity,
            'get_tota_qty':self.get_tota_qty,
            'get_total_capacity':self.get_total_capacity,
            'get_title':self.get_title,
            'get_qty_string':self.get_qty_string,
            'get_do':self.get_do,
            'get_total_bag':self.get_total_bag,
            'get_capacity':self.get_capacity
        })
        return localcontext
    
    def get_do(self,line):
        do_ids = []
        for i in line:
            for j in i.delivery_ids:
                if j.id not in do_ids:
                    do_ids.append(j.id)
        return self.env['delivery.order'].browse(do_ids)
    
    def get_qty_string(self,line):
        com = self.env['res.company'].search([], limit = 1)
        qty =  self.get_tota_qty(line)
        chuoi = com.with_context(lang='vi_VN').second_currency_id.amount_to_text(qty)   
        chuoi = chuoi.replace(u'đồng',u'kilogram')
        chuoi = chuoi[0].upper() + chuoi[1:]
        return chuoi
    
    
    def get_date(self, date):
        if not date:
            date = datetime.now()
        date_user_tz = self.env['res.users']._convert_user_datetime(
            fields.Datetime.to_string(date))
        
        date = date_user_tz.strftime('%d/%m/%Y')
        return date
    
    def get_header(self):
        wizard_data = self.localcontext['data']['model']
        return self.env['delivery.order'].browse(wizard_data)
    
    def get_capacity(self,o):
        if o.delivery_order_ids[0].packing_id and o.delivery_order_ids[0].packing_id.capacity:
            return round(o.total_qty / o.delivery_order_ids[0].packing_id.capacity,0)
        else:
            return 0
        
    def get_title(self):
        wizard_data = self.localcontext['data']['model']
        wizard_data = wizard_data and wizard_data[0] or False
        return self.env['delivery.order'].browse(wizard_data)
    
    def get_total_bag(self,line):
        do_ids = []
        total_bag =0.0
        for i in line:
            for j in i.delivery_ids:
                if j.id not in do_ids:
                    do_ids.append(j.id)
        for k in self.env['delivery.order'].browse(do_ids):
            if k.delivery_order_ids[0].packing_id and k.delivery_order_ids[0].packing_id.capacity:
                total_bag += round(k.total_qty / k.delivery_order_ids[0].packing_id.capacity,0)
        return total_bag
    
    def get_tota_qty(self,line):
        do_ids = []
        total_qty =0.0
        for i in line:
            for j in i.delivery_ids:
                if j.id not in do_ids:
                    do_ids.append(j.id)
        for k in self.env['delivery.order'].browse(do_ids):
            total_qty += k.total_qty
        return total_qty
    
    def get_total_capacity(self):
        wizard_data = self.localcontext['data']['model']
        qty =0.0
        for delivery in self.env['delivery.order'].browse(wizard_data):
            for line in delivery.delivery_order_ids:
                if line.packing_id and line.packing_id.capacity:
                    qty += round(delivery.total_qty / line.packing_id.capacity,0)
                else:
                    qty += line.product_qty
        return qty
    
    


