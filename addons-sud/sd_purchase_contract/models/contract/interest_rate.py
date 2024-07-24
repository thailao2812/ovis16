# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
import time

class InterestRate(models.Model): 
    _name = "interest.rate"
    
    month = fields.Selection([('1', 'Tháng 1'), ('2', 'Tháng 2'),  ('3', 'Tháng 3'),
                              ('4', 'Tháng 4'),  ('5', 'Tháng 5')], string='Months',
                             readonly=False, copy=False, index=True,)
    rate = fields.Float(string ="Rate %",digits=(12, 3))
    request_id = fields.Many2one('request.payment', string='Request payment')
    
    def _compute_provisional_rate(self,date=None):
        if not date:
            current_date = time.strftime(DATE_FORMAT)
        else:
            current_date =date
        for request in self:
            provisional_rate =0.0
            if request.request_id:
                for payment in request.request_id.request_payment_ids:
                    days = 0
                    allocation_amount =0.0
                    payment_date = payment.date
                    sql ='''
                        SELECT sum(allocation_amount) allocation_amount
                        FROM payment_allocation
                        WHERE
                            pay_id =%s
                    '''%(payment.id)
                    self.env.cr.execute(sql)
                    for allocation in self.env.cr.dictfetchall():
                        allocation_amount = allocation['allocation_amount'] or 0.0
                    
                    
                    amount = (payment.amount - allocation_amount) /30
                    if request.month in ('1','2','3','4'):
                        if request.month == '1':
                            sql = '''
                            SELECT '%s'::Date - '%s'::Date as days
                        '''%(current_date , payment_date)
                        elif request.month == '2':
                            sql = '''
                                SELECT '%s'::Date - ('%s'::Date + 30) as days
                            '''%(current_date , payment_date)
                        elif request.month == '3':
                            sql = '''
                                SELECT '%s'::Date - ('%s'::Date + 60) as days
                            '''%(current_date , payment_date)
                        else:
                            sql = '''
                                SELECT '%s'::Date - ('%s'::Date + 90) as days
                            '''%(current_date , payment_date)
                             
                        self.env.cr.execute(sql)
                        for da in self.env.cr.dictfetchall():
                            days = da['days']
                         
                        if days>0 and days <=30:
                            amount = amount * days * request.rate/100
                        elif days >30:
                            amount = amount * 30 * request.rate/100
                        else:
                            amount = 0
                        
                        provisional_rate += amount
                    else:
                        sql = '''
                            SELECT '%s'::Date - ('%s'::Date + 120) as days
                        '''%(current_date, payment_date)
                        self.env.cr.execute(sql)
                        for da in self.env.cr.dictfetchall():
                            days = da['days']
                        
                        if days>0 :
                            amount = amount * days * request.rate/100
                        else:
                            amount = 0
                        provisional_rate += amount
                    
            request.provisional_rate =  provisional_rate       
    
    provisional_rate = fields.Float(string='Lãi tạm tính',compute='_compute_provisional_rate',digits=(12, 0))
    
    
    ################################ NED ContRACT vn ##################################     ##################################

    contract_id = fields.Many2one('purchase.contract', related='request_id.purchase_contract_id', store=True)
    date = fields.Date(string='Date start')
    date_end = fields.Date(string='Date End')
    
    
    ################################ end NED ContRACT vn ##################################     ##################################

    
    