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
    _name = 'report.nvp_liquidation_report'
    _inherit = ['report.report_aeroo.abstract']
    _description = 'report.nvp_liquidation_report'
    

    def _set_localcontext(self):
        localcontext = super(Parser, self)._set_localcontext()
        global bank_name 
        global partner 
        global account_holder 
        global acc_number
        
        bank_name = False
        partner = False 
        account_holder = False 
        acc_number = False
        
        global rate_1 
        global rate_2 
        global rate_3 
        global rate_4 
        global rate_5 
        
        rate_1 = 0.0
        rate_2 = 0.0
        rate_3 = 0.0
        rate_4 = 0.0
        rate_5 = 0.0
        
        localcontext.update({
            'get_account_holder':self.get_account_holder,
            'get_bank_name':self.get_bank_name,
            'get_acc_number':self.get_acc_number,
            'get_string_amount':self.get_string_amount,
            'get_date':self.get_date,
            'get_rate1':self.get_rate1,
            'get_rate2':self.get_rate2,
            'get_rate3':self.get_rate3,
            'get_rate4':self.get_rate4,
            'get_rate5':self.get_rate5,
            'get_sum_interest_amount':self.get_sum_interest_amount,
            'get_total_payable':self.get_total_payable,
            'get_asv':self.get_asv,
            'get_lina':self.get_lina,
            'get_todate':self.get_todate,
            'get_pay':self.get_pay,
            'get_sum_interest_amount_ung':self.get_sum_interest_amount_ung
        })
        return localcontext
    
    def get_pay(self,o):
        pay =0.0
        for line in o.payment_ids:
            if not line.request_payment_id:
                continue
            pay += line.amount
        for allotion in o.pay_allocation_ids:
            pay += allotion.allocation_amount
        return pay
            
    def get_todate(self):
        date = time.strftime(DATE_FORMAT)
        date = datetime.strptime(date, DATE_FORMAT)
        return date.strftime('%d/%m/%Y')
    
    def get_lina(self,payment_line):
        val =[]
        for line in payment_line:
            if line.total_interest_pay >0:
                val.append({
                            'name':line.pay_id.request_payment_id.purchase_contract_id.name,
                            'allocation_amount':line.allocation_amount,
                            'payment_date':line['payment_date'],
                            'id':line.id,
                            'total_interest_pay':line.total_interest_pay
                })
        
        return val
    
    def get_total_payable(self,a,b):
        return a-b 
    
    def get_account_holder(self,partner):
        if not account_holder:
            get_partner_banks(partner)
        return account_holder or ''
    
    def get_bank_name(self,partner):
        if not bank_name:
            self.get_partner_banks(partner)
        return bank_name or ''


    def get_asv(self,name):
        partner = self.env['res.partner'].search([('name','=',name)])
        return partner.child_ids and partner.child_ids[0].name or ''
    
    def get_string_amount(self, o):
        chuoi = o.company_id.with_context(lang='vi_VN').second_currency_id.amount_to_text(abs(o.amount_total))
        chuoi = chuoi[0].upper() + chuoi[1:]
        return chuoi
    
    def get_acc_number(self,partner):
        if not acc_number:
            self.get_partner_banks(partner)
        return acc_number or ''
    
    def get_partner_banks(self,partner):
        sql ='''
            SELECT rp.name account_holder, rb.name bank_name,acc_number,* 
            FROM res_partner_bank rpb join res_bank rb on rpb.bank_id = rb.id 
                join res_partner rp on rpb.partner_id= rp.id
            WHERE partner_id = %s
        '''%(partner.id)
        self.cr.execute(sql)
        for line in self.cr.dictfetchall():
            account_holder = line['account_holder']
            bank_name = line['bank_name']
            acc_number = line['acc_number']
            
    def get_date(self, date):
        if not date:
            date = datetime.now()
        date_user_tz = self.env['res.users']._convert_user_datetime(
            fields.Datetime.to_string(date))
        
        date = date_user_tz.strftime('%d/%m/%Y')
        return date
    
    def get_rate1(self,interest_id):
        self.get_line_interest_rate(interest_id)
        return rate_1
    def get_rate2(self,interest_id):
        self.get_line_interest_rate(interest_id)
        return rate_2
    def get_rate3(self,interest_id):
        self.get_line_interest_rate(interest_id)
        return rate_3
    def get_rate4(self,interest_id):
        self.get_line_interest_rate(interest_id)
        return rate_4
    def get_rate5(self,interest_id):
        self.get_line_interest_rate(interest_id)
        return rate_5
        
    def get_sum_interest_amount(self,pay_allocation_ids):
        amount =0.0
        for line in pay_allocation_ids:
            for allocation_line in line.allocation_line_ids:
                amount += allocation_line.actual_interest_pay
        return amount

    def get_sum_interest_amount_ung(self,pay_allocation_ids):
        amount =0.0
        for line in pay_allocation_ids:
            amount += line.allocation_amount
        return amount
    
    def get_line_interest_rate(self,pay_allocation_id):
        sql ='''
            SELECT sum(thang1) thang1,sum(thang2) thang2,
                sum(thang3) thang3,sum(thang4) thang4,
                sum(thang5) thang5
            FROM (
                SELECT rate thang1,0.0 thang2,0.0 thang3,0.0 thang4, 0.0 thang5
                FROM payment_allocation_line where pay_allocation_id = %(pay_allocation_id)s and month ='1'
                union all
                SELECT 0.0 thang1,rate thang2,0.0 thang3,0.0 thang4, 0.0 thang5
                FROM payment_allocation_line where pay_allocation_id = %(pay_allocation_id)s and month ='2'
                union all
                SELECT 0.0 thang1,0.0 thang2,rate thang3,0.0 thang4, 0.0 thang5
                FROM payment_allocation_line where pay_allocation_id = %(pay_allocation_id)s and month ='3'
                union all
                SELECT 0.0 thang1,0.0 thang2,0.0 thang3,rate thang4, 0.0 thang5
                FROM payment_allocation_line where pay_allocation_id = %(pay_allocation_id)s and month ='4'
                union all
                SELECT 0.0 thang1,0.0 thang2,0.0 thang3,0.0 thang4,rate thang5
                FROM payment_allocation_line where pay_allocation_id = %(pay_allocation_id)s and month ='5'
            )x
        '''%({
              'pay_allocation_id': pay_allocation_id,
              }) 
        self.cr.execute(sql)
        for line in self.cr.dictfetchall():
            rate_1 = line['thang1'] or 0.0
            rate_2 = line['thang2'] or 0.0
            rate_3 = line['thang3'] or 0.0
            rate_4 = line['thang4'] or 0.0
            rate_5 = line['thang5'] or 0.0
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
