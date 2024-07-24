# -*- encoding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.addons.report_aeroo.report_parser import Parser

import datetime
import time
import pytz
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime, timedelta, date

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


class Parser(models.AbstractModel):
    _name = 'report.npe_report'
    _inherit = ['report.report_aeroo.abstract']
    _description = 'report.npe_report'
    

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
            'get_asv':self.get_asv,
            'get_songay':self.get_songay,
            'centificate':self.centificate,
            'centificavn':self.centificavn,
            'centificaen':self.centificaen,
            'get_license': self.get_license
        })
        return localcontext
    
    
    def centificavn(self,o):
        if o.certificate_id:
            return u'Đạt chứng nhận '+o.certificate_id.code
        else:
            return ''
    
    def centificaen(self,o):
        if o.certificate_id:
            return o.certificate_id.code+ ' certified.'
        
        else:
            return ''
    def centificate(self,o):
        line =[]
        if o.certificate_id:
            line.append({
                        'code':o.certificate_id.code
            })
            return line
        return line
    
    def get_songay(self,date,so_ngay):
        return self.get_date( o.date_order + timedelta(days=o.so_ngay))
    
    def get_asv(self,name):
        partner = self.env['res.partner'].search([('name','=',name)])
        return partner.child_ids and partner.child_ids[0].name or ''
    
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

    def get_license(self, purchase):
        if purchase:
            if purchase.license_id:
                return purchase.license_id.name[:-5]
            else:
                return ''
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
