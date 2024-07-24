# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

    
class PaymentAllocation(models.Model):
    _name = "payment.allocation"
    _order = 'id desc'
    
    def npe_nvp_entries(self):
        for contract in self.contract_id:
            move_obj = self.env['account.move']
            debit_account_id = contract.partner_id.property_account_payable_id.id
            credit_account_id = contract.partner_id.property_vendor_advance_acc_id.id
            journal_id = self.env['account.journal'].search([('type', '=', 'purchase')], limit=1)
            allocation_amount =0.0
            if self.pay_id.extend_payment == 'advance':
                allocation_amount = self.allocation_amount or 0.0
            if not allocation_amount:
                return False
            
            name = u'''Kết chuyển tạm ứng %s - %s'''%(self.pay_id.purchase_contract_id.name,contract.name)
            move_lines = contract._prepare_account_move_line_for_general(allocation_amount, credit_account_id, debit_account_id,name)
            date = contract.date_order
            new_move_id = move_obj.create({'journal_id': journal_id.id,
                                      'account_analytic_id':contract.warehouse_id and contract.warehouse_id.account_analytic_id.id,
                                      'line_ids': move_lines,
                                      'date': date,
                                      'ref': name,
                                      'narration':name})
            new_move_id.action_post()
        return new_move_id.id
    
    def update_npe_nvp_entries(self):
        for contract in self.contract_id:
            move_obj = self.env['account.move']
            debit_account_id = contract.partner_id.property_account_payable_id.id
            credit_account_id = contract.partner_id.property_vendor_advance_acc_id.id
            journal_id = self.env['account.journal'].search([('type', '=', 'purchase')], limit=1)
            allocation_amount =0.0
            if self.pay_id.extend_payment == 'advance':
                allocation_amount = self.allocation_amount or 0.0
            if not allocation_amount:
                return False
            
            name = u'''Kết chuyển tạm ứng %s - %s'''%(self.pay_id.purchase_contract_id.name,contract.name)
            move_lines = contract._prepare_account_move_line_for_general(allocation_amount, credit_account_id, debit_account_id,name)
            return move_lines
    
    @api.model
    def create(self, vals):
        result = super(PaymentAllocation, self).create(vals)
        return result
    
    def write(self, vals):
        result = super(PaymentAllocation, self).write(vals)
        return result
    
    def _compute_payment_received(self):
        for line in self:
            if line.pay_id:
                pay_alocation = 0.0
                
                
                payment = self.env['payment.allocation'].search([('pay_id','=',line.pay_id.id)])
                pay_alocation = sum(payment.mapped('allocation_amount')) or 0.0
            
                # sql='''
                #     SELECT sum(allocation_amount) amount
                #     FROM payment_allocation
                #     WHERE pay_id = %s
                # '''%(line.pay_id.id)
                # self.env.cr.execute(sql)
                # for pay in self.env.cr.dictfetchall():
                #     pay_alocation = pay['amount'] or 0.0
                
                line.payment_received = pay_alocation
                line.payment_remain = line.payment_amount - pay_alocation
                if line.payment_remain == 0:
                    line.pay_id.write({'allocated':True})
                else:
                    line.pay_id.write({'allocated':False})
            else:
                line.payment_received = 0
                line.payment_remain =0
                 
    def _compute_total_interest_pay(self):
        for line in self:
            amount = 0.0
            for payline in line.allocation_line_ids:
                payline._compute_interest_pay()
                amount += payline.actual_interest_pay
            line.total_interest_pay = amount
    
    pay_id = fields.Many2one('account.payment', string='Payment')
    #notes = fields.Char(related='pay_id.notes', string='notes')
    request_id = fields.Many2one(related='pay_id.request_payment_id', string='Request', readonly=True)
    partner_id = fields.Many2one(related='pay_id.partner_id', string='Supplier', readonly=True,store=True)
    relation_contract_id = fields.Many2one(related='pay_id.purchase_contract_id', string='From NPE', readonly=True)
    payment_date = fields.Date(related='pay_id.payment_date', string='Payment Date', readonly=True)
    payment_amount = fields.Monetary(related='pay_id.amount', string='Original Amount', readonly=True,currency_field='currency_id')
    currency_id = fields.Many2one(related='pay_id.currency_id', string='Currency', readonly=True)
    contract_id = fields.Many2one('purchase.contract', string='To NVP')
    allocation_amount = fields.Float('Allocation Amount',digits=(12, 0))
    allocation_line_ids = fields.One2many('payment.allocation.line', 'pay_allocation_id', string='Allocation Line')
    
    payment_received = fields.Float(compute='_compute_payment_received', string='Refunded', readonly=True,digits=(12, 0))
    payment_remain = fields.Float(compute='_compute_payment_received', string='Open Advance', readonly=True,digits=(12, 0))
    total_interest_pay = fields.Float(compute='_compute_total_interest_pay', string='Interest', readonly=True,digits=(12, 0))
    
    nvp_date = fields.Date(related='contract_id.date_order', string='NVP Date', readonly=True)
    
    move_id = fields.Many2one('account.move',string="Entries")
    
    
    def get_vietname_date(self, date):
        if not date:
            date = time.strftime(DATE_FORMAT)
        date = datetime.strptime(date, DATE_FORMAT)
        return date.strftime('%d-%m-%Y')
    
    @api.depends('nvp_date')
    def _compute_date(self):
        for line in self:
            line.date_tz = line.nvp_date
            line.day_tz = self.get_vietname_date(line.nvp_date)
            
    date_tz = fields.Date(string = "date", store=True)
    day_tz = fields.Char(string = "Month", store=True)
    
    def btt_load_interest(self):
        interest_obj = self.env['payment.allocation.line']
        # if self.allocation_amount == 0:
        #     raise UserError(
        #         _("Please Input Allocation Amount before Load Interest") 
        #     )
        for allocation_line in self:
            allocation_line.allocation_line_ids.unlink()
            payment = allocation_line.pay_id.id
            request_payment = allocation_line.relation_contract_id.mapped('request_payment_ids').filtered(
                lambda x: payment in x.request_payment_ids.ids)
            for rate in request_payment.rate_ids:
                if not rate.date or not rate.date_end:
                    raise UserError(_("You need to full fill Date From - Date To for Rate in Request Payment NPE"))
                value = {
                    'from_date': rate.date,
                    'to_date': rate.date_end,
                    'rate': rate.rate,
                    'pay_allocation_id': allocation_line.id,
                }
                interest_obj.create(value)
                allocation_line.read()
                #Kiet goi hàm tính lãi ngày
                interest_obj._compute_interest_pay()
  
class PaymentAllocationLine(models.Model):
    _name = "payment.allocation.line"
    _order = 'id desc'   
    
    @api.model
    def create(self, vals):
        result = super(PaymentAllocationLine, self).create(vals)
        return result

    @api.depends('pay_allocation_id.allocation_amount', 'pay_allocation_id','rate', 'from_date', 'to_date')
    def _compute_interest_pay(self):
        for line in self:
            # line.pay_allocation_id.read()
            total_date = 0.0
            # sql = '''
            #     SELECT '%s'::date - '%s'::date as date 
            # ''' % (line.to_date, line.from_date)
            # self.env.cr.execute(sql)
            # for rate in self.env.cr.dictfetchall():
            #     date = total_date = rate['date'] 
            
            total_date = date = (line.to_date - line.from_date).days
             
            interest_pay = line.pay_allocation_id.allocation_amount * (line.rate /100)
            if total_date == 0:
                date = 0
                total_date = 0
                interest_pay_one = (interest_pay / 30) * int(date)
            else:
#                 if date !=30:
#                     date -= 1
#                     total_date -=1
                interest_pay_one = (interest_pay / 30) * int(date)
             
            line.update({
                'total_date': total_date,
                'interest_pay': interest_pay ,
                'actual_interest_pay': interest_pay_one,
            })
     
    pay_allocation_id = fields.Many2one('payment.allocation', string='Pay Allocation Line')
    from_date = fields.Date(string='From Date', readonly=True)
    to_date = fields.Date(string='To Date', readonly=True)
    amount_interest_rate = fields.Monetary(string='Amount Interest', readonly=True)
    currency_id = fields.Many2one(related='pay_allocation_id.contract_id.currency_id', string='Currency', readonly=True)
    total_date = fields.Integer(compute='_compute_interest_pay', string='Date', readonly=True, store=True)
    interest_pay = fields.Float(compute='_compute_interest_pay', string='Interest Pay/Month', readonly=True, store=True,digits=(12, 0))
    actual_interest_pay = fields.Float(compute='_compute_interest_pay', string='Interest pay/Day', readonly=True, store=True,digits=(12, 0))
    month = fields.Selection([('1', 'Tháng 1'), ('2', 'Tháng 2'),  ('3', 'Tháng 3'),
                              ('4', 'Tháng 4'),  ('5', 'Tháng 5')], string='Month',
                             readonly=False, copy=False, index=True,)
    rate = fields.Float(string='Rate %', readonly=False,digits=(12, 6))