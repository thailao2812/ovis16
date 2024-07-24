# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

class AccountPayment(models.Model):
    _inherit = "account.payment"
    
    # def delete_payment(self):
    #     for i in self.env['account.payment'].search([('date','>=','2023-04-01'),('date','<=','2023-04-30'),('api','=',True)]):
    #         i.action_draft()
    #         i.unlink()
    
    
    def action_draft(self):
        self.move_id.posted_before = False
        self.move_id.name ='/'
        res = super(AccountPayment, self).action_draft()
        return res
 
    
    @api.depends('journal_id', 'payment_type', 'payment_method_line_id')
    def _compute_outstanding_account_id(self):
        for pay in self:
            if pay.payment_type == 'inbound':
                # pay.outstanding_account_id = (pay.payment_method_line_id.payment_account_id
                #                               or pay.journal_id.company_id.account_journal_payment_debit_account_id)
                
                pay.outstanding_account_id = pay.journal_id.default_account_id.id
                
                
            elif pay.payment_type == 'outbound':
                # pay.outstanding_account_id = (pay.payment_method_line_id.payment_account_id
                #                               or pay.journal_id.company_id.account_journal_payment_credit_account_id)
                
                pay.outstanding_account_id = pay.journal_id.default_account_id.id
            else:
                pay.outstanding_account_id = False
    
    outstanding_account_id = fields.Many2one(
        comodel_name='account.account',
        string="Outstanding Account",
        store=True,
        compute='_compute_outstanding_account_id',
        check_company=True)
                
                
    
    extend_payment = fields.Selection([
        ('payment', 'Payment'),
        ('advance', 'Advance'),
    ],  default='payment', string='Payment Mode', readonly=True, states={'draft': [('readonly', False)]})
    
    responsible = fields.Char(string='Responsible')
    
    communication = fields.Char(string="Memo", store=True, readonly=False)
    
    @api.depends('account_analytic_id')
    def _get_company_analytic_account_id(self):
        company_analytic_account = False
        company_analytic_account = self.env['account.analytic.account'].search([('id', 'parent_of', self.account_analytic_id.ids), 
                                                                                    ('analytic_type','=','2')])
            
        self.company_analytic_account_id = company_analytic_account
        
        
    company_analytic_account_id = fields.Many2one('account.analytic.account', 'Company Analytic Account', 
                                                  compute='_get_company_analytic_account_id',
                                                  readonly=True, index=True, store=True)
    #Kiệt bỏ
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account', readonly=True, index=True, store=True)
    
    
    currency_rate = fields.Float(string='Payment Currency Rate', copy=False, default=1, readonly=True, states={'draft': [('readonly', False)]})
    
    #THANH: this dummy field help to check currency_rate must be input if invoice_currency_id != payment_currency_id
    invoice_currency_id = fields.Many2one('res.currency', string='Invoice Currency', copy=False)
    
    conversion_currency_id = fields.Many2one('res.currency', string='Conversion Currency', copy=False, readonly=True, 
                                             states={'draft': [('readonly', False)]})
    conversion_currency_rate = fields.Float(string='Conversion Currency Rate', copy=False, default=1, readonly=True, 
                                            states={'draft': [('readonly', False)]})
    conversion_currency_amount = fields.Monetary(string='Conversion Currency Amount', copy=False, readonly=True, 
                                                 currency_field='conversion_currency_id', 
                                                 states={'draft': [('readonly', False)]})
    
    @api.onchange('conversion_currency_rate')
    def _onchange_conversion_currency_rate(self):
        if self.amount and self.conversion_currency_id and self.conversion_currency_rate:
            if not self.conversion_currency_rate > 1:
                self.conversion_currency_rate = hasattr(self, '_origin') and self._origin.conversion_currency_rate or 1.0
                message = _("Conversion Currency Rate %s must be greater than 1.")%(self.conversion_currency_id.name)
                warning = {
                   'title': _('Payment Method!'),
                   'message' : message
                }
                return {'warning': warning}
                                                    
    @api.onchange('conversion_currency_rate','conversion_currency_id','amount')
    def _onchange_conversion_currency_id(self):
        if self.amount and self.conversion_currency_id and self.conversion_currency_rate and self.conversion_currency_rate > 1:
            self.conversion_currency_amount = self.currency_id.\
                                                with_context(currency_rate=self.conversion_currency_rate).\
                                                    compute(self.amount, self.conversion_currency_id)
    
    @api.constrains('invoice_currency_id', 'currency_id', 'currency_rate')
    def _check_currency_rate(self):
        if self.invoice_currency_id and self.currency_id and (self.invoice_currency_id != self.currency_id != self.company_id.currency_id):
            raise UserError(_("Payment Currency '%s' is not supported in case it's difference to Invoice Currency '%s' and Company Currency '%s'.\nPayment Currency should be '%s' or '%s'")%\
                            (self.currency_id.name, self.invoice_currency_id.name, self.company_id.currency_id.name, self.invoice_currency_id.name, self.company_id.currency_id.name))
        
        #THANH: check currency type to input rate
        if self.invoice_currency_id and self.invoice_currency_id != self.currency_id and not self.currency_rate > 1:
            raise UserError(_("Currency Rate %s must be greater than 1.")%(self.currency_id.name))
        
    
    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        if self.journal_id:
            if self.invoice_currency_id and self.currency_id and (self.invoice_currency_id != self.currency_id != self.company_id.currency_id):
                self.journal_id = False
                self.currency_id = False
                message = _("Payment Currency '%s' is not supported in case it's difference to Invoice Currency '%s' and Company Currency '%s'.\nPayment Currency should be '%s' or '%s'")%\
                                (self.currency_id.name, self.invoice_currency_id.name, self.company_id.currency_id.name, self.invoice_currency_id.name, self.company_id.currency_id.name)
                warning = {
                   'title': _('Payment Method!'),
                   'message' : message
                }
                return {'warning': warning}
    
    
#     @api.depends('invoice_ids', 'payment_type', 'partner_type', 'partner_id')
#     def _compute_destination_account_id(self):
#         if self.invoice_ids:
#             self.destination_account_id = self.invoice_ids[0].account_id.id
#         elif self.payment_type == 'transfer':
#             #THANH: No need to raise this error
# #             if not self.company_id.transfer_account_id.id:
# #                 raise UserError(_('Transfer account not defined on the company.'))
#             #THANH: get account from destination journal account
#             self.destination_account_id = self.destination_journal_id.default_debit_account_id.id or self.destination_journal_id.default_credit_account_id.id
#             #self.company_id.transfer_account_id.id
#         elif self.partner_id:
#             #THANH: When this is advance payment will get other account in partner
#             if self.partner_type == 'customer':
#                 if self.extend_payment == 'payment':
#                     self.destination_account_id = self.partner_id.property_account_receivable_id.id
#                 else:
#                     self.destination_account_id = self.partner_id.property_customer_advance_acc_id.id
#             else:
#                 if self.extend_payment == 'payment':
#                     self.destination_account_id = self.partner_id.property_account_payable_id.id
#                 else:
#                     self.destination_account_id = self.partner_id.property_vendor_advance_acc_id.id
                    
    
    
    #THANH: Show Invoices Number
    # @api.depends('invoice_ids.state', 'show_invoice', 'payment_lines')
    # def _get_invoice_number(self):
    #     res = ''
    #     if len(self.invoice_ids):
    #         for inv in self.invoice_ids:
    #             if inv.state not in ['draft', 'cancel'] and (inv.reference or inv.number):
    #                 if inv.reference and inv.reference != '/':
    #                     res += inv.reference and _('%s, ')%(inv.reference) or ''
    #                 else:
    #                     res += inv.number and _('%s, ')%(inv.number) or '' 
    #     if len(self.payment_lines) and self.show_invoice:
    #         for inv in self.payment_lines:
    #             if inv.number:
    #                 res += inv.number and _('%s, ')%(inv.number) or ''  
    #     if len(res):
    #         self.invoice_reference = res[:-2]
            
    invoice_reference = fields.Char(string="Invoice Number", readonly=True, store=True)
    
    @api.depends('invoice_currency_id', 'currency_id')
    def _check_diff_currency(self):
        if self.invoice_currency_id and self.currency_id:
            self.diff_currency = self.invoice_currency_id != self.currency_id
        else:
            self.diff_currency = False
            
    #THANH: new field to hide tab company currency
    diff_currency = fields.Boolean(string='Diff Currency', readonly=True, compute='_check_diff_currency')

    def action_draft(self):
        self.move_id.posted_before = False
        self.move_id.name = '/'
        res = super(AccountPayment, self).action_draft()
        return res
    
    
                    