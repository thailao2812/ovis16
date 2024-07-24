# -*- encoding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError
from datetime import datetime
from datetime import date

import time
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%d-%m-%Y"
# -*- encoding: utf-8 -*-


class Parser(models.AbstractModel):
    _name = 'report.report_stock_kcs_qa_gdn'
    _inherit = ['report.report_aeroo.abstract']
    _description = 'report.report_stock_kcs_qa_gdn'
    
    def _set_localcontext(self):
        localcontext = super(Parser, self)._set_localcontext()
        
        localcontext.update({
            'get_date':self.get_date,
            'get_maize':self.get_maize,
            'get_printf':self.get_printf,
            'get_printf_dates':self.get_printf_dates
        })
        return localcontext
    
    
    def get_maize(self,line):
        if not line:
            return 'N'
        if line[0].maize_yn:
            return'Y'
        else:
            return 'N'
        
    def get_printf(self):
        return self.env.user.name
    
    def get_printf_dates(self):
        now = datetime.now()
        strs = str(now.hour) +":" + str(now.minute) +" "+str(now.day) +"/"+str(now.month) +"/"+str(now.year)
        return strs
            
    def get_date(self, date):
        if not date:
            date = datetime.now()
        date_user_tz = self.env['res.users']._convert_user_datetime(
            fields.Datetime.to_string(date))
        date = date_user_tz.strftime('%d/%m/%Y')
        return date
    
    


