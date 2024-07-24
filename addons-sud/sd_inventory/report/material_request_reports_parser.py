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
    _name = 'report.report_material_request_reports'
    _inherit = ['report.report_aeroo.abstract']
    _description = 'report.report_material_request_reports'
    
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
            'get_stack':self.get_stack,
            'get_stack_quality':self.get_stack_quality
        })
        return localcontext
    
    def get_to_be_issued(self,re_qty,isue_qty):
        return re_qty - isue_qty
    
    def get_issued_qty(self,request_id):
        line = self.env['request.materials.line'].browse(request_id)
        return line.basis_qty
    
    def get_stack_qty(self,request_id):
        line = self.env['request.materials.line'].browse(request_id)
        return line.stack_id.init_qty
    
    def get_zone(self,request_id):
        line = self.env['request.materials.line'].browse(request_id)
        return line.stack_id.zone_id.name 
    
    def get_stack(self,request_id):
        line = self.env['request.materials.line'].browse(request_id)
        return line.stack_id.code or line.stack_id.name
    
    def get_stack_quality(self,request_id):
        line = self.env['request.materials.line'].browse(request_id)
        return line.stack_id
    
    
    def get_line(self, obj):
        if obj.production_ids:
            sql ='''
                SELECT rml.id request_id,mrp.name name_mrp, rm.name rm_name,rm.request_date, pp.default_code,
                rml.product_qty request_qty,rml.state,
                    lot.mc,
                    lot.fm,
                    lot.black,
                    lot.broken,
                    lot.brown,
                    lot.mold,
                    lot.cherry,
                    lot.excelsa,
                    lot.screen20,
                    lot.screen19,
                    lot.screen18,
                    lot.screen17,
                    lot.screen16,
                    lot.screen15,
                    lot.screen14,
                    lot.screen13,
                    lot.greatersc12,
                    lot.screen12,
                    lot.immature,
                    lot.burn,
                    lot.eaten,
                    lot.stone_count,
                    lot.stick_count,
                    lot.remarks,
                    pack.name as packing
                    
                FROM request_materials rm 
                    join request_materials_line rml on rm.id =  rml.request_id
                    join stock_lot lot on lot.id =  rml.stack_id
                    join product_product pp on rml.product_id = pp.id
                    join mrp_production mrp on mrp.id = rm.production_id
                    left join ned_packing pack on rml.packing_id = pack.id
                WHERE mrp.id in (%s)
            '''%(','.join(map(str, obj.production_ids.ids)))
        else:
            sql ='''
                SELECT rml.id request_id,mrp.name name_mrp, rm.name rm_name,rm.request_date, pp.default_code,
                rml.product_qty request_qty,rml.state,
                    lot.mc,
                    lot.fm,
                    lot.black,
                    lot.broken,
                    lot.brown,
                    lot.mold,
                    lot.cherry,
                    lot.excelsa,
                    lot.screen20,
                    lot.screen19,
                    lot.screen18,
                    lot.screen17,
                    lot.screen16,
                    lot.screen15,
                    lot.screen14,
                    lot.screen13,
                    lot.greatersc12,
                    lot.screen12,
                    lot.immature,
                    lot.burn,
                    lot.eaten,
                    lot.stone_count,
                    lot.stick_count,
                    lot.remarks,
                    pack.name as packing
                    
                FROM request_materials rm 
                    join request_materials_line rml on rm.id =  rml.request_id
                    join product_product pp on rml.product_id = pp.id
                    join stock_lot lot on lot.id =  rml.stack_id
                    join mrp_production mrp on mrp.id = rm.production_id
                    left join ned_packing pack on rml.packing_id = pack.id
                WHERE rm.request_date between '%s' and '%s'
            '''%(obj.from_date,obj.to_date)
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
