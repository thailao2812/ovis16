# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

    
class AccountPayment(models.Model):
    _inherit = "account.payment"
    _description = "Payments"
    
    request_payment_id = fields.Many2one('request.payment', string='Reason')
    payment_date = fields.Date(string="Date")
    ###################### SUC Contract ###################################################################################################
    
    
    
    def action_post(self):
        res = super(AccountPayment, self).action_post()
        active_id = self._context.get('active_id')
        # if self._context.get('active_model') and self._context.get('active_model') ==  'purchase.contract':
        #     contract_id = self.env[self._context.get('active_model')].browse(active_id)
            
                
        
        if self.purchase_contract_id:
            if not self.request_payment_id:
                if self.purchase_contract_id.type != 'purchase':
                    self.purchase_contract_id.write({'state':'done'})
                    return res
                
                self.purchase_contract_id.write({
                    'date_payment_final': self.date or False
                })
                date_final_payment = self.purchase_contract_id.date_payment_final
                
                if self.purchase_contract_id.interest_move_id:
                    sql = '''
                        DELETE from account_move_line where move_id = %s 
                    '''%(self.purchase_contract_id.interest_move_id.id)
                    self.env.cr.execute(sql)
                    self.purchase_contract_id.interest_move_id.write({'line_ids': self.purchase_contract_id.update_advance_interest_entries()})
                    
                if not self.purchase_contract_id.interest_move_id:
                    interest_move_id = self.purchase_contract_id.advance_interest_rate_entries()
                    self.purchase_contract_id.write({'interest_move_id': interest_move_id})

                self.purchase_contract_id.interest_move_id.date = date_final_payment
                for i in self.purchase_contract_id.interest_move_id.line_ids:
                    i.date = date_final_payment
                
                if self.purchase_contract_id.type != 'purchase':
                    self.purchase_contract_id.write({'state':'done'})
                    return res
                
                if self.purchase_contract_id.interest_move_entries_id:
                    return res
                
                # date_final_payment = self.purchase_contract_id.date_payment_final
                new_id = self.purchase_contract_id.done_interest_rate_entries()
                account_move = self.env['account.move'].browse(new_id)
                if new_id:
                    self.purchase_contract_id.write({'interest_move_entries_id': new_id})
                    account_move.write({
                        # 'doc_date': date_final_payment,
                        'date': date_final_payment
                    })
                    for line in account_move.line_ids:
                        line.date = date_final_payment
                

        return res
    
    def unlink(self):
        # Cập nhật xóa ngày final Payment trên Purchase Contract
        if self.purchase_contract_id:
            if not self.request_payment_id:
                self.purchase_contract_id.date_payment_final = False
                
        res = super(AccountPayment, self).unlink()
        return res
    
    @api.model
    def default_get(self, fields): 
        rec = super(AccountPayment, self).default_get(fields)
        active_id = self._context.get('active_id')
        if self._context.get('active_model') and self._context.get('active_model') == 'request.payment':
            request = self.env['request.payment'].browse(active_id)
            if request.purchase_contract_id:
                rec['currency_id'] = request.purchase_contract_id.currency_id.id
                rec['payment_type'] = 'outbound'
                rec['partner_id'] = request.purchase_contract_id.partner_id.id
                rec['purchase_contract_id'] = request.purchase_contract_id.id
                rec['request_payment_id'] =  active_id
                rec['responsible'] = self.env.user.name
                
                
                request_amount = 0
                for payment in request.request_payment_ids.filtered(lambda x: x.state == 'posted'):
                    request_amount += payment.amount 
                
                rec['amount'] = request.request_amount - (request_amount or 0.0)
                
                if request.purchase_contract_id.type not in ('purchase','ptbf'):
                    rec['extend_payment'] = 'payment'
                    rec['ref'] = u'Tạm ứng theo ' + request.purchase_contract_id.name
                else:
                    rec['extend_payment'] = 'payment'
                    rec['ref'] = u'Thanh toán tiền theo ' + request.purchase_contract_id.name
                    
                    
                # if request.purchase_contract_id.type !='purchase':
                #     # rec['extend_payment'] = 'advance'
                #     rec['extend_payment'] = 'payment'
                #     rec['ref'] = 'Advance - ' + request.purchase_contract_id.name
                # else:
                #     rec['extend_payment'] = 'payment'
                #     rec['ref'] = 'Payment - ' + request.purchase_contract_id.name
        
        if self._context.get('active_model') and self._context.get('active_model') == 'purchase.contract':
            contract_id = self.env[self._context.get('active_model')].browse(active_id)
            if contract_id.type == 'purchase':
                rec['currency_id'] = contract_id.currency_id.id
                rec['payment_type'] = 'outbound'
                rec['partner_id'] = contract_id.partner_id.id
                rec['purchase_contract_id'] = contract_id.id
                rec['ref'] = u'Thanh toán tiền theo ' + contract_id.name
                rec['extend_payment'] = 'payment'
                rec['amount'] = contract_id.amount_total
            
            if contract_id.type == 'ptbf':
                rec['ref'] = contract_id.name
                rec['currency_id'] = contract_id.currency_id.id
                rec['payment_type'] = 'outbound'
                rec['partner_id'] = contract_id.partner_id.id
                rec['purchase_contract_id'] = contract_id.id
                rec['communication'] = u'Nhận đặt cọc tiền theo ' + contract_id.name
                rec['extend_payment'] = 'payment'
                rec['amount'] = contract_id.amount_total
                
                
        return rec
    
    purchase_contract_id = fields.Many2one('purchase.contract', string='Purchase Contract',
       readonly=True, states={'draft': [('readonly', False)]}, required=False,)
    
    allocated = fields.Boolean(string = 'Allocated',default=False)
    ###################### END Bes Contract ###################################################################################################
    ###################### NED Contract ###################################################################################################

    def _create_payment_entry(self, amount):
        move_id = super(AccountPayment, self)._create_payment_entry(amount)
        if self.purchase_contract_id:
            self.purchase_contract_id.move_ids = [(4, move_id.id)]
    
    @api.depends('state')
    def _compute_payment_received(self):
        for line in self:
            pay_alocation = 0.0
            
            payment = self.env['payment.allocation'].search([('pay_id','=',line.id)])
            pay_alocation = sum(payment.mapped('allocation_amount'))
            
            # sql='''
            #     SELECT sum(allocation_amount) amount
            #     FROM payment_allocation
            #     WHERE pay_id = %s
            # '''%(line.id)
            # self.env.cr.execute(sql)
            # for pay in self.env.cr.dictfetchall():
            #     pay_alocation = pay['amount'] or 0.0
            line.payment_refunded = pay_alocation
            line.open_advance = line.amount - pay_alocation
    
        
    payment_refunded = fields.Float(compute='_compute_payment_received', string='Refunded', readonly=True,digits=(12, 0), store = True)
    open_advance = fields.Float(compute='_compute_payment_received', string='Open Advance', readonly=True,digits=(12, 0), store = True)

    ###################### END NED Contract ###################################################################################################
    
    ###################### BESCO ACCOUNT ###################################################################################################

    extend_payment = fields.Selection([
        ('payment', 'Payment'),
        ('advance', 'Advance'),
    ],  default='payment', string='Payment Mode', readonly=True, states={'draft': [('readonly', False)]})
    
    ###################### BESCO NED Contract ###################################################################################################


    