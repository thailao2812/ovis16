# -*- encoding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.addons.report_aeroo.report_parser import Parser

import datetime
import time
import pytz
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

bank_name =False
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
    _name = 'report.stock_balancesheet_nxct_report'
    _inherit = ['report.report_aeroo.abstract']
    _description = 'report.stock_balancesheet_nxct_report'
    
    def _set_localcontext(self):
        localcontext = super(Parser, self)._set_localcontext()
        
        localcontext.update({
            'get_line':self.get_line,
            'get_vietname_date':self.get_vietname_date,
            'get_date':self.get_date,
            'get_location':self.get_location
        })
        return localcontext
    
    def get_location(self, object):
        location_name = False
        for lo in  object.location_ids:
            location_name = lo.name
        return location_name
    
    def get_date(self, date):
        if not date:
            date = datetime.now()
            
        date_user_tz = self.env['res.users']._convert_user_datetime(
            fields.Datetime.to_string(date))
        return date_user_tz.strftime('%d/%m/%Y')
    
    def get_vietname_date(self, date):
        if not date:
            date = datetime.now()
            
        date_user_tz = self.env['res.users']._convert_user_datetime(
            fields.Datetime.to_string(date))
        return date_user_tz.strftime('%d/%m/%Y')
    
    def get_line(self, product_id, object):
        res =[]
        location_id = False

        lines = self.env['report.stock.balance.sheet.line'].search([(['report_id','=',object.id]),('product_id','=',product_id)])
        bg_qty =  lines.bg_qty or 0.0
        bg_value =  lines.bg_value or 0.0
        for lo in  object.location_ids:
            location_id = lo.id
        sql ='''
            SELECT * FROM (
            SELECT 'xuat' type_s,sm.product_id,sm.date,sp.name,sm.reference, 0 nhap_qty ,0 nhap_gia, qty_done xuat_qty, price_unit xuat_gia
            FROM stock_move_line sm left join stock_picking sp on sm.picking_id = sp.id 
            where sm.location_id = %s and sm.location_dest_id != %s
            and sm.state ='done'
            union all
            SELECT 'nhap' type_s, sm.product_id,sm.date,sp.name, sm.reference, qty_done nhap_qty,price_unit nhap_gia ,0 xuat_qty ,0 xuat_gia
                FROM stock_move_line sm left join stock_picking sp on sm.picking_id = sp.id 
                where sm.location_id != %s and sm.location_dest_id = %s
            and sm.state ='done'
            )x
            where x.product_id = %s and date(timezone('UTC',date::timestamp)) between '%s' and '%s' 
            order by date
        '''%(location_id,location_id,location_id,location_id,product_id,object.date_start,object.date_end)
        self.env.cr.execute(sql)
        for i in self.env.cr.dictfetchall():
            contract = ''
            reference = ''
            if i['type_s']== 'xuat':
                bg_qty -= i['xuat_qty']
                if i['xuat_gia'] is None:
                    bg_value -= i['xuat_qty'] * 0
                    i['xuat_gia'] = 0
                else:
                    bg_value -= i['xuat_qty'] * i['xuat_gia']
            else:
                bg_qty += i['nhap_qty']
                if i['nhap_gia'] is None:
                    bg_value += i['nhap_qty'] * 0
                    i['nhap_gia'] = 0
                else:
                    bg_value += i['nhap_qty'] * i['nhap_gia']
                if i['name'] and ('IM' in i['name'] or 'FA/INT' in i['name']):
                    picking = self.env['stock.picking'].search([('name','=',i['name'])])
                    if ';' in picking.origin:
                        a = picking.origin.split(';')
                        contract = a and a[1] or ''
                        reference= a and a[0] or ''
                    else:
                        contract = picking.origin or ''
                
            res.append({
                        'date':self.get_vietname_date(i['date']),
                        'name':i['name'],
                        'contract':contract or '',
                        'reference':reference or '',
                        'origin':i['reference'],
                        'nhap_qty':i['nhap_qty'],
                        'nhap_gia':i['nhap_gia'],
                        'xuat_qty':i['xuat_qty'],
                        'xuat_gia':i['xuat_gia'],
                        'ton_qty':bg_qty,
                        'ton_value':bg_value,
                        'don_gia_ton':bg_qty and bg_value/bg_qty or 0.0
                        })
        return res
    
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
