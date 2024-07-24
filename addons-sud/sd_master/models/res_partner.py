# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

class ResPartner(models.Model):
    _inherit = "res.partner"
    
    transfer = fields.Boolean(string='Is a Transporters')
    
    is_customer_coffee = fields.Boolean(string='Is Customer Coffee', default=False)
    is_supplier_coffee = fields.Boolean(string='Is Supplier Coffee', default=False)
    position_en = fields.Char(string="Position (EN)",size=256)
    
    # supplier_mgt_line = fields.One2many('supplier.mgt','partnert_id','Supplier Mgt')
    type_ned = fields.Selection([('normal', 'Normal'), ('partner', 'Partner')], string='Type', default='normal')
    repperson1 = fields.Char(string='RepPerson1')
    repperson2 = fields.Char(string='RepPerson2')
    goods = fields.Selection([('faq', 'FAQ'), ('grade', 'GRADE')], string='Goods')
    ppkg = fields.Float(string='PPKg')
    
    estimated_annual_volume = fields.Float(string='Estimated Annual Volume')
    purchase_undelivered_limit = fields.Float(string='Purchase Undelivered Limit')
    property_evaluation = fields.Float(string='Property Evaluation')
    m2mlimit = fields.Float(string='M2MLimit')
    partner_code = fields.Char(string="Partner Code")
    district_id = fields.Many2one('res.district', string="District")
    fax =fields.Char(string="fax")
    shortname = fields.Char(string="shortname")

    # accounting_type = fields.Selection([
    #     ('coffee_export', 'Coffee Export'),
    #     ('coffee_local', 'Coffee Local'),
    #     ('expense', 'Expense')
    # ], string='Accounting Type')

    # @api.onchange('accounting_type')
    # def onchange_accounting_type(self):
    #     if self.accounting_type:
    #         if self.accounting_type == 'coffee_export':
    #             account_1st = self.env['account.account'].search([('code', '=', '13111')])
    #             account_2nd = self.env['account.account'].search([('code', '=', '3312')])
    #             account_3rd = self.env['account.account'].search([('code', '=', '3312')])
    #             account_4th = self.env['account.account'].search([('code', '=', '13112')])
    #             self.property_account_receivable_id = account_1st.id
    #             self.property_account_payable_id = account_2nd.id
    #             self.property_vendor_advance_acc_id = account_3rd.id
    #             self.property_customer_advance_acc_id = account_4th.id
    #         if self.accounting_type == 'coffee_local':
    #             account_1st = self.env['account.account'].search([('code', '=', '1314')])
    #             account_2nd = self.env['account.account'].search([('code', '=', '3312')])
    #             account_3rd = self.env['account.account'].search([('code', '=', '3312')])
    #             account_4th = self.env['account.account'].search([('code', '=', '1314')])
    #             self.property_account_receivable_id = account_1st.id
    #             self.property_account_payable_id = account_2nd.id
    #             self.property_vendor_advance_acc_id = account_3rd.id
    #             self.property_customer_advance_acc_id = account_4th.id
    #         if self.accounting_type == 'expense':
    #             account_1st = self.env['account.account'].search([('code', '=', '1313')])
    #             account_2nd = self.env['account.account'].search([('code', '=', '3311')])
    #             account_3rd = self.env['account.account'].search([('code', '=', '3311')])
    #             account_4th = self.env['account.account'].search([('code', '=', '1313')])
    #             self.property_account_receivable_id = account_1st.id
    #             self.property_account_payable_id = account_2nd.id
    #             self.property_vendor_advance_acc_id = account_3rd.id
    #             self.property_customer_advance_acc_id = account_4th.id

    
    
    #
    # def name_get(self):
    #     result = []
    #     res = super(ResPartner, self).name_get()
    #     for pro in self:
    #         result.append((pro.id, pro.code))
    #     return res