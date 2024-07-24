# -*- encoding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.addons.report_aeroo.report_parser import Parser
from datetime import datetime, timedelta, date

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



class Parser(models.AbstractModel):
    _name = 'report.nvp_report'
    _inherit = ['report.report_aeroo.abstract']
    _description = 'report.nvp_report'
    

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
            'get_npe_nvl':self.get_npe_nvl,
            'get_songay':self.get_songay,
            'centificate':self.centificate,
            'centificavn':self.centificavn,
            'centificaen':self.centificaen,
            'get_datefix':self.get_datefix,
            'get_fixation_deadline':self.get_fixation_deadline,
            'get_month':self.get_month,
            'get_datefix_end':self.get_datefix_end,
            'convert_month':self.convert_month,
            'get_name_vn':self.get_name_vn,
            'get_name_en':self.get_name_en,
            'get_rool_text':self.get_rool_text,
            'get_date_en':self.get_date_en,
            'get_myear': self.get_myear,
            'get_cert': self.get_cert,
            'get_license': self.get_license
        })
        return localcontext
    
    
    def get_rool_text(self,roll_id):
        vn = vn1 = en = en1 =''
        if roll_id:
            vn1 += _(self.get_month(roll_id.date_fixed))
            en1 += _(self.convert_month(roll_id.date_fixed)) + _(roll_id.date_fixed)[2:4]
            if roll_id.contract_id.rolling_ids.sorted(key=lambda l: l.date,reverse=True).filtered(lambda x: x.date < roll_id.date):
                roll_before_id =roll_id.contract_id.rolling_ids.sorted(key=lambda l: l.date,reverse=True).filtered(lambda x: x.date <= roll_id.date)[0]
                vn += _(self.get_month(roll_before_id.date_fixed))
                en += _(self.convert_month(roll_before_id.date_fixed)) + _(roll_before_id.date_fixed)[2:4]
                if roll_before_id.diff_price < 0:
                    vn += u' trừ lùi '+u'%s'%(_(abs(int(roll_before_id.diff_price))))
                    vn += u'$/tấn (' +u'%s-%s'%(_(self.convert_month(roll_before_id.date_fixed)) + _(roll_before_id.date_fixed)[2:4],_(abs(int(roll_before_id.diff_price))))
                    vn +=u'$/Mt)'
                    en +=u' in London LIFFE minus (-) %s'%(_(abs(roll_before_id.diff_price)))
                    en +=u'$/Mt'
                else:
                    vn += u' công thêm '+u'%s'%(_(abs(int(roll_before_id.diff_price))))
                    vn += u'$/tấn (' +u'%s+%s'%(_(self.convert_month(roll_before_id.date_fixed)) + _(roll_before_id.date_fixed)[2:4],_(abs(int(roll_before_id.diff_price))))
                    vn +=u'$/Mt)'
                    en +=u' in London LIFFE plus (+) %s'%(_(abs(int(roll_before_id.diff_price))))
                    en +=u'$/Mt'
            else:
                roll_before_id =roll_id.contract_id.contract_line[0]
                vn += _(self.get_month(roll_id.contract_id.date_fix))
                en += _(self.convert_month(roll_id.contract_id.date_fix)) + _(roll_id.contract_id.date_fix)[2:4]
                if roll_before_id.diff_price < 0:
                    vn += u' trừ lùi '+u'%s'%(_(abs(int(roll_before_id.diff_price))))
                    vn += u'$/tấn (' +u'%s-%s'%(_(self.convert_month(roll_id.contract_id.date_fix)) + _(roll_id.contract_id.date_fix)[2:4],_(abs(int(roll_before_id.diff_price))))
                    vn +=u'$/Mt)'
                    en +=u' in London LIFFE minus (-) %s'%(_(abs(roll_before_id.diff_price)))
                    en +=u'$/Mt'
                else:
                    vn += u' công thêm '+u'%s'%(_(abs(int(roll_before_id.diff_price))))
                    vn += u'$/tấn (' +u'%s+%s'%(_(self.convert_month(roll_id.contract_id.date_fix)) + _(roll_id.contract_id.date_fix)[2:4],_(abs(int(roll_before_id.diff_price))))
                    vn +=u'$/Mt)'
                    en +=u' in London LIFFE plus (+) %s'%(_(abs(roll_before_id.diff_price)))
                    en +=u'$/Mt'
            if roll_id.diff_price < 0:
                vn1 += u' trừ lùi '+u'%s'%(_(abs(int(roll_id.diff_price))))
                vn1 += u'$/tấn (' +u'%s-%s'%(_(self.convert_month(roll_id.date_fixed)) + _(roll_id.date_fixed)[2:4],_(abs(int(roll_id.diff_price))))
                vn1 +=u'$/Mt)'
                en1 +=u' in London LIFFE minus (-) %s'%(_(abs(roll_id.diff_price)))
                en1 +=u'$/Mt'
            else:
                vn1 += u' cộng thêm '+u'%s'%(_(abs(int(roll_id.diff_price))))
                vn1 += u'$/tấn (' +u'%s+%s'%(_(self.convert_month(roll_id.date_fixed)) + _(roll_id.date_fixed)[2:4],_(abs(int(roll_id.diff_price))))
                vn1 +=u'$/Mt)'
                en1 +=u' in London LIFFE plus (+) %s'%(_(abs(roll_id.diff_price)))
                en1 +=u'$/Mt'
        return{'vn':vn,
               'vn1':vn1,
               'en':en,
               'en1':en1}
            
    def get_cert(self, cert_id):
        result = ''
        if cert_id:
            result = cert_id.name.split(' ')[0]
            if cert_id.name == '4C FC':
                result = '4C Nestle Farmer Connect.'
        return result

                
    def get_datefix(self,date_fix):
        if not date_fix:
            return ''
        sql ='''
            select '%s'::date -10 as date_fix
        '''%(date_fix)
        self.cr.execute(sql)
        for line in self.cr.dictfetchall():
            return self.get_date(line['date_fix'])
        return ''

    def get_fixation_deadline(self, fixation_deadline):
        if not fixation_deadline:
            fixation_deadline = time.strftime(DATE_FORMAT)
        fixation_deadline = datetime.strptime(fixation_deadline, DATE_FORMAT)
        return fixation_deadline.strftime('%d/%m/%Y')    
    
    def get_name_vn(self,product):
        if product.code == 'FAQ':
            return u'Cà phê nhân xô'
        elif product.code == 'S13-ST':
            return u'Cà phê thành phẩm G2, 5% đen vỡ'
        elif product.code == 'S16-ST':
            return u'Cà phê thành phẩm G1, sàng 16, 2% đen vỡ'
        elif product.code == 'S18-ST':
            return u'Cà phê thành phẩm G1, sàng 18, 2% đen vỡ'
        else:
            return u'Cà phê nhân xô'
    
    def get_name_en(self,product):
        if product.code == 'FAQ':
            return u'Vietnam Robusta FAQ Coffee Bean'
        elif product.code == 'S13-ST':
            return u'G2, 5%BB'
        elif product.code == 'S16-ST':
            return u'G1, S16, 2%BB'
        elif product.code == 'S18-ST':
            return u'G1, S18, 2%BB' 
        else:
            return u'Cà phê nhân xô'
        
        
    def get_datefix_end(self,date_fix):
        if not date_fix:
            date_fix = time.strftime(DATE_FORMAT)
        else:
            sql ='''
                select '%s'::date -10 as date_fix
            '''%(date_fix)
            self.cr.execute(sql)
            for line in self.cr.dictfetchall():
                date= date = datetime.strptime(line['date_fix'], DATE_FORMAT) 
        return date.strftime("%d %b %y")
    
    def convert_month(self,date_fix):
        if not date_fix:
            date_fix = time.strftime(DATE_FORMAT)
        date = datetime.strptime(date_fix, DATE_FORMAT)
        a = date.strftime('%m')
        if date.strftime('%m') in ('01','02'):
            return 'F'
        if date.strftime('%m') in ('03','04'):
            return 'H'
        if date.strftime('%m') in ('05','06'):
            return 'K'
        if date.strftime('%m') in ('07','08'):
            return 'N'
        if date.strftime('%m') in ('09','10'):
            return 'U'
        if date.strftime('%m') in ('11','12'):
            return 'X'
    
    def get_myear(self,date_fix):
        if not date_fix:
            date_fix = datetime.now()
        date_user_tz = self.env['res.users']._convert_user_datetime(fields.Datetime.to_string(date_fix))
        
        if date_user_tz.strftime('%m') in ('01','02'):
            return 'F%s'%str(date_user_tz.strftime('%y'))
        if date_user_tz.strftime('%m') in ('03','04'):
            return 'H%s'%str(date_user_tz.strftime('%y'))
        if date_user_tz.strftime('%m') in ('05','06'):
            return 'K%s'%str(date_user_tz.strftime('%y'))
        if date_user_tz.strftime('%m') in ('07','08'):
            return 'N%s'%str(date_user_tz.strftime('%y'))
        if date_user_tz.strftime('%m') in ('09','10'):
            return 'U%s'%str(date_user_tz.strftime('%y'))
        if date_user_tz.strftime('%m') in ('11','12'):
            return 'X%s'%str(date_user_tz.strftime('%y'))
        return 1
    
    def get_month(self,date_fix):
        if not date_fix:
            date_fix = datetime.now()
        date_fix = self.env['res.users']._convert_user_datetime(
            fields.Datetime.to_string(date_fix))
        
        return date_fix.strftime('%m/%Y')
    
    def centificavn(self,o):
        if o.certificate_id:
            return u'Đạt chứng nhận '+o.certificate_id.code
        else:
            return ''
    
    def centificaen(self,o):
        if o.certificate_id:
            return o.certificate_id.code + ' certified.'
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
    
    def get_npe_nvl(self,o):
        printf =''
        for line in o.nvp_ids:
            for j in line.npe_contract_id.npe_ids:
                if j.contract_id.id == o.id:
                    printf += line.npe_contract_id.name + ': ' +str(int(j.product_qty)) +' Kg; '
        return printf
    
    
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
        users =self.pool.get('res.users').browse(self.cr,self.uid,SUPERUSER_ID)
        chuoi = users.amount_to_text(o.amount_sub_total, 'vn')
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
    
        
    
    def get_date_en(self, date):
        if not date:
            date = datetime.now()
        date_user_tz = self.env['res.users']._convert_user_datetime(
            fields.Datetime.to_string(date))
        return date_user_tz.strftime('%d %b %Y')
    
    def get_songay(self,o):
        return self.get_date(o.date_order + timedelta(days=o.so_ngay))
        # sql ='''
        #     SELECT '%s'::date + %s as songay
        # '''%(o.date_order,o.so_ngay)
        # self.cr.execute(sql)
        # for line in self.cr.dictfetchall():
        #     return self.get_date(line['songay'])

    def get_license(self, purchase):
        if purchase:
            if purchase.license_id:
                return purchase.license_id.name[:-5]
            else:
                return ''
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
