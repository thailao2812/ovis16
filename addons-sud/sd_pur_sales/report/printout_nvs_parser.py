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
    _name = 'report.printout_nvs_report'
    _inherit = ['report.report_aeroo.abstract']
    _description = 'report.printout_nvs_report'
    
    

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
            'get_account_holder':self.get_account_holder,
            'get_bank_name':self.get_bank_name,
            'get_acc_number':self.get_acc_number,
            'get_string_amount':self.get_string_amount,
            'get_date':self.get_date,
            'get_term': self.get_term,
            'get_date_mos':self.get_date_mos,
            'get_dates_mos':self.get_dates_mos
        })
        return localcontext
    
    def get_account_holder(self,partner):
        if not self.account_holder:
            self.get_partner_banks(partner)
        return self.account_holder or ''
    
    def get_bank_name(self,partner):
        if not self.bank_name:
            self.get_partner_banks(partner)
        return self.bank_name or ''
    
    def get_string_amount(self, o):
        users =self.pool.get('res.users').browse(self.cr,self.uid,SUPERUSER_ID)
        return users.amount_to_text(o.request_amount, 'vn')
    
    def get_acc_number(self,partner):
        if not self.acc_number:
            self.get_partner_banks(partner)
        return self.acc_number or ''
    
    def get_partner_banks(self,partner):
        sql ='''
            SELECT rp.name account_holder, rb.name bank_name,acc_number,* 
            FROM res_partner_bank rpb join res_bank rb on rpb.bank_id = rb.id 
                join res_partner rp on rpb.partner_id= rp.id
            WHERE partner_id = %s
        '''%(partner.id)
        self.cr.execute(sql)
        for line in self.cr.dictfetchall():
            self.account_holder = line['account_holder']
            self.bank_name = line['bank_name']
            self.acc_number = line['acc_number']
            
    def get_date(self, date):
        if not date:
            date = datetime.now()
        date_user_tz = self.env['res.users']._convert_user_datetime(
            fields.Datetime.to_string(date))
        
        return date_user_tz.strftime('%d/%m/%Y')
    
    def get_date_mos(self, date):
        if not date:
            date = datetime.now()
        date_user_tz = self.env['res.users']._convert_user_datetime(
            fields.Datetime.to_string(date))
        return date_user_tz.strftime('%b, %Y')
    
    def get_dates_mos(self, date):
        if not date:
            date = datetime.now()
        date_user_tz = self.env['res.users']._convert_user_datetime(
            fields.Datetime.to_string(date))
        
        return date_user_tz.strftime('%b, %d, %Y')
    
    
    def get_term(self, status):
        if status in ('fOB','FOB'):
            term = 'FOB'
        else:
            term = 'Allocated'
        return term
    
    


