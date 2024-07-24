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
    _name = 'report.report_s_contract'
    _inherit = ['report.report_aeroo.abstract']
    _description = 'report.report_s_contract'
    
    

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
            'get_dates_mos':self.get_dates_mos,
            'get_shipt_weights':self.get_shipt_weights,
            'get_container_status':self.get_container_status,
            'get_string_selection': self.get_string_selection,
            'get_data_document_contract': self.get_data_document_contract
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
            return True
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
    
    def get_shipt_weights(self, weights):
        if weights == 'DW':
            shipt_weights = 'Delivered Weights'
        elif weights == 'NSW':
            shipt_weights = 'Net Shipped Weights'
        elif weights == 'NLW':
            shipt_weights = 'Net Landed Weights'
        else:
            shipt_weights = 'Re Weights'
        return shipt_weights

    def get_container_status(self, container):
        if container == 'fcl/fcl':
            status = 'FCL/FCL'
        elif container == 'lcl/fcl':
            status = 'LCL/FCL'
        elif container == 'lcl/lcl':
            status = 'LCL/LCL'
        else:
            status = ''
        return status

    def get_string_selection(self, s_contract):
        if s_contract:
            return dict(s_contract._fields['arbitration'].selection).get(s_contract.arbitration)

    def get_data_document_contract(self, s_contract):
        if s_contract:
            return ', '.join(i.name for i in s_contract.document_contract)
