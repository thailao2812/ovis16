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
    _name = 'report.report_print_request_materials'
    _inherit = ['report.report_aeroo.abstract']
    _description = 'report.report_print_request_materials'
    
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
            'get_line':self.get_line,
            'get_destart':self.get_destart,
            'get_destrt':self.get_destrt,
            'get_issued_qty':self.get_issued_qty,
            'get_to_be_issued':self.get_to_be_issued,
            'get_stack_qty':self.get_stack_qty,
            'get_zone':self.get_zone,
            'get_stack':self.get_stack
        })
        return localcontext
    
    def get_to_be_issued(self,re_qty,isue_qty):
        return re_qty - isue_qty
    
    def get_issued_qty(self,request_id):
        line = self.pool.get('request.materials.line').browse(self.cr,self.uid,request_id)
        return line.basis_qty
    
    def get_stack_qty(self,request_id):
        line = self.pool.get('request.materials.line').browse(self.cr,self.uid,request_id)
        return line.stack_id.init_qty
    
    def get_zone(self,request_id):
        line = self.pool.get('request.materials.line').browse(self.cr,self.uid,request_id)
        return line.stack_id.zone_id.name 
    
    def get_stack(self,request_id):
        line = self.pool.get('request.materials.line').browse(self.cr,self.uid,request_id)
        return line.stack_id.code or line.stack_id.name
    
    def get_line(self, obj):
        if obj.production_ids:
            sql ='''
                SELECT mrp.name mrp_name,re.name request_name,sp.name pick_name,pp.default_code,zone.name zone_name,
                    sta.name stack_name,sp.total_init_qty re_qty,sp.total_qty qty,
                    sp.total_init_qty, sp.total_bag, sp.total_init_qty-sp.total_init_qty in_store,
                    date(timezone('UTC',sp.date_done ::timestamp)) date_issue         
                FROM stock_picking sp 
                    join  picking_request_move_ref refs on sp.id = refs.request_id 
                    join request_materials_line line on line.id = refs.picking_id
                    join request_materials re on re.id = line.request_id
                    join mrp_production mrp on mrp.id = re.production_id
                    join product_product pp on pp.id = line.product_id
                    left join stock_lot zone on zone.id = sp.zone_id
                    join stock_lot sta on sta.id = sp.stack_id
                    where mrp.id in (%s)
                          and sp.state ='done'
            '''%(','.join(map(str, obj.production_ids.ids)))
        else:
            sql ='''
                SELECT mrp.name mrp_name,re.name request_name,sp.name pick_name,pp.default_code,zone.name zone_name,
                    sta.name stack_name,sp.total_init_qty  re_qty,sp.total_qty qty,
                    sp.total_init_qty, sp.total_bag, sp.total_init_qty-sp.total_init_qty in_store,
                    date(timezone('UTC',sp.date_done ::timestamp)) date_issue         
                FROM stock_picking sp 
                    join  picking_request_move_ref refs on sp.id = refs.request_id 
                    join request_materials_line line on line.id = refs.picking_id
                    join request_materials re on re.id = line.request_id
                    join mrp_production mrp on mrp.id = re.production_id
                    join product_product pp on pp.id = line.product_id
                    left join stock_zone zone on zone.id = sp.zone_id
                    join stock_lot sta on sta.id = sp.stack_id
                    where date(timezone('UTC',sp.date_done ::timestamp)) between '%s' and '%s'
                          and sp.state ='done'
            '''%(obj.from_date,obj.to_date)
        print(sql)
        self.env.cr.execute(sql)
        return self.env.cr.dictfetchall()
    
    def get_destart(self, obj):
        # self.get_header(obj)
        return self.get_date(obj.from_date)
    
    def get_destrt(self , obj):
        # self.get_header()
        return self.get_date(obj.to_date)
        
    def get_date(self, date):
        if not date:
            date = datetime.now()
        date_user_tz = self.env['res.users']._convert_user_datetime(
            fields.Datetime.to_string(date))
        return date_user_tz.strftime('%d/%m/%Y')
    
    def get_datetime(self, date):
        if not date:
            date = time.strftime(DATETIME_FORMAT)
        date = datetime.strptime(date, DATETIME_FORMAT)
        return date.strftime('%d/%m/%Y')
    
    
    def get_header(self, obj):
        from_date = obj.from_date
        to_date = obj.to_date
        production_id = obj.production_id
        return True
    
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
