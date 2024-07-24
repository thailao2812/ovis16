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
    _name = 'report.report_grp'
    _inherit = ['report.report_aeroo.abstract']
    _description = 'report.report_grp'
    
    def _set_localcontext(self):
        localcontext = super(Parser, self)._set_localcontext()
        global from_date 
        global to_date 
        global production_id 
        
        from_date = False
        to_date = False
        production_id = False
        
        
        localcontext.update({
            'get_date':self.get_date,
            'get_datetime':self.get_datetime,
            'total_bb':self.total_bb,
            'total_sc16':self.total_sc16,
            'gross_weight':self.gross_weight,
            'get_printf':self.get_printf,
            'get_printf_dates':self.get_printf_dates,
            'get_maize':self.get_maize,
            'get_do':self.get_do,
            'get_nvs':self.get_nvs,
            'get_grp':self.get_grp,
            'makeQRcode':self.makeQRcode,
            'get_first_weight':self.get_first_weight,
            'get_second_weight':self.get_second_weight,
            'get_bag_no':self.get_bag_no,
            'get_gross_weight':self.get_gross_weight,
            'get_init_qty':self.get_init_qty,
            'get_tare_weight':self.get_tare_weight,
            'get_packing':self.get_packing,
            'get_contract_ids':self.get_contract_ids,
        })
        return localcontext
    
    def get_contract_ids(self,o):
        picking_id = o.id
        o.write({'total_print_grn':o.total_print_grn + 1})
        if o.backorder_id:
            picking_id = o.backorder_id.id
        res = []
#         for allocation in self.pool.get('stock.allocation').search(self.cr, self.uid,[('picking_id','=',picking_id)]):
#             allocation_id = self.pool.get('stock.allocation').browse(self.cr, self.uid,allocation)
#             res.append({'contract_name':allocation_id.contract_id and allocation_id.contract_id.name or '',
#                         'qty':allocation_id.contract_id and allocation_id.contract_id.qty_allocate or 0})
        if not res:
            i =1
            while i < 4:
                res.append({'contract_name':'',
                        'qty':''})
                i +=1
        return res
        
    def get_first_weight(self,o):
        return sum(o.move_line_ids_without_package.mapped('first_weight')) or 0
    
    def get_second_weight(self,o):
        return sum(o.move_line_ids_without_package.mapped('second_weight')) or 0
    
    def get_bag_no(self,o):
        return sum(o.move_line_ids_without_package.mapped('bag_no')) or 0
    
    def get_gross_weight(self,o):
        return sum(o.move_line_ids_without_package.mapped('init_qty')) + sum(o.move_line_ids_without_package.mapped('tare_weight'))
    
    def get_init_qty(self,o):
        return sum(o.move_line_ids_without_package.mapped('init_qty'))
    
    def get_tare_weight(self,o):
        return sum(o.move_line_ids_without_package.mapped('tare_weight'))
    
    def get_packing(self,o):
        return ', \n'.join(map(str, [x.packing_id.name for x in o.move_line_ids_without_package])) 
    
    
    def get_maize(self,line):
        if not line:
            return 'N'
        if line[0].maize_yn:
            return'Y'
        else:
            return 'N'
    
        
    def get_printf(self):
        users = self.env['res.users'].browse(self.env.uid)
        return users.name
    
    def get_printf_dates(self):
        now = datetime.now()
        strs = str(now.hour) +":" + str(now.minute) +" "+str(now.day) +"/"+str(now.month) +"/"+str(now.year)
        return strs
    
    def get_date(self, date):
        if not date:
            date = datetime.now()
            
        date_user_tz = self.env['res.users']._convert_user_datetime(
            fields.Datetime.to_string(date))
        return date_user_tz.strftime('%d/%m/%Y')
    
    def get_datetime(self, date):
        if not date:
            date = datetime.now()
        
        date_user_tz = self.env['res.users']._convert_user_datetime(
            fields.Datetime.to_string(date))
        # date = str(res_user._convert_user_datetime(self.cr,self.uid,date))
        # date = datetime.strptime(date[0:19], DATETIME_FORMAT)
        return date_user_tz.strftime('%d/%m/%Y %H:%M:%S')
    
    def gross_weight(self,line):
        if not line:
            return 0
        return (line[0].first_weight - line[0].second_weight) or 0.0
    
    def total_bb(self,line):
        if not line:
            return 0
        return line[0].black + line[0].broken
    
    def total_sc16(self,line):
        if not line:
            return 0
        return line.screen18 + line.screen16
    
    def get_do(self,o):
        sql ='''
            SELECT id from delivery_order where picking_id = %s
        '''%(o.id)
        self.cr.execute(sql)
        for line in self.cr.dictfetchall():
            delivery = self.pool.get('delivery.order').browse(self.cr,self.uid,line['id'])
            return delivery and delivery.name or ''
    
    def get_nvs(self,o):
        sql ='''
            SELECT id from delivery_order where picking_id = %s
        '''%(o.id)
        self.cr.execute(sql)
        for line in self.cr.dictfetchall():
            delivery = self.pool.get('delivery.order').browse(self.cr,self.uid,line['id'])
            return delivery and delivery.contract_id.name or ''
    
    def get_grp(self,line):
        if line.stack_id:
            for stack_line in line.stack_id.move_ids:
                if stack_line.location_id.usage !='internal' and stack_line.location_dest_id.usage == 'internal':
                    return stack_line.picking_id.name
        
        return ''
            
    
    def makeQRcode(self, name=None, size=2):
        self.name = name
        self.size = size
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=size)
        qr.add_data(name)
        qr.make(fit=True)
        im = qr.make_image()
        tf = StringIO()
        im.save(tf, 'png')
        size_x = str(im.size[0]/96.0)+'in'
        size_y = str(im.size[1]/96.0)+'in'

        return tf, 'image/png', size_x, size_y
    
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
