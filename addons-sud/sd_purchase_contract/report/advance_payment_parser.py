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
    _name = 'report.advance_payment_report'
    _inherit = ['report.report_aeroo.abstract']
    _description = 'report.advance_payment_report'
    

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
        
        localcontext.update({
            'get_account_holder':self.get_account_holder,
            'get_bank_name':self.get_bank_name,
            'get_acc_number':self.get_acc_number,
            'get_string_amount':self.get_string_amount,
            'get_date':self.get_date,
            'get_rate': self.get_rate,
            'get_date_end': self.get_date_end,
            'get_total_qty': self.get_total_qty,
            'get_songay':self.get_songay
        })
        return localcontext
    
    def get_date(self, date):
        if not date:
            date = datetime.now()
        date_user_tz = self.env['res.users']._convert_user_datetime(
            fields.Datetime.to_string(date))
        
        date = date_user_tz.strftime('%d/%m/%Y')
        return date
    
    
    def get_songay(self,date,so_ngay):
        # sql ='''
        #     SELECT '%s'::date + %s as songay
        # '''%(date,so_ngay)
        # self.env.cr.execute(sql)
        # for line in self.cr.dictfetchall():
        #     return self.get_date(line['songay'])
        return self.get_date(date + timedelta(days=so_ngay))
        
    def get_account_holder(self,partner):
        if not account_holder:
            self.get_partner_banks(partner)
        return account_holder or ''
    
    def get_bank_name(self,partner):
        if not bank_name:
            self.get_partner_banks(partner)
        return bank_name or ''
    
    def get_string_amount(self, o):
        chuoi = o.company_id.with_context(lang='vi_VN').second_currency_id.amount_to_text(o.request_amount)
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
        self.env.cr.execute(sql)
        for line in self.env.cr.dictfetchall():
            account_holder = line['account_holder']
            bank_name = line['bank_name']
            acc_number = line['acc_number']
        return
            
    
    def get_rate(self, request_id):
        rate = 0.0
        if not request_id:
            return rate
        
        rate_obj = self.env['interest.rate'].search([('request_id','=',request_id),('month','=','1')])
        return rate_obj and rate_obj.rate or 0.0
            
        # sql ='''
        #     SELECT rate 
        #     FROM interest_rate 
        #     WHERE request_id = %s
        #     AND month = '1'
        # '''%(request_id)
        # self.env.cr.execute(sql)
        # result = self.env.cr.dictfetchall()
        # rate = result and result[0] and result[0]['rate'] or 0.0
        # return rate
    
    def get_date_end(self, date):
        if not date:
            date = datetime.now()
        date = datetime.strptime(date, DATE_FORMAT)
        date_end = date + timedelta(days=120)
        date_end = date_end.strftime('%d/%m/%Y')
        return date_end

    def get_total_qty(self, purchase_contract_id):
        total_qty = 0.0
        if not purchase_contract_id:
            return total_qty
        sql ='''
            SELECT sum(sm.qty_done) total_qty
            FROM stock_picking sp join stock_move_line sm on sm.picking_id = sp.id
            WHERE sp.state = 'done' AND sp.purchase_contract_id = %s
        '''%(purchase_contract_id)
        self.cr.execute(sql)
        result = self.env.cr.dictfetchall()
        total_qty = result and result[0] and result[0]['total_qty'] or 0.0
        return total_qty
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
