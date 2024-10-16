# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class PurchaseContract(models.Model):
    _inherit = 'purchase.contract'

    list_farmer = fields.One2many('list.farmer', 'purchase_contract_id')

    equiv_faq_price = fields.Float(string='Equiv. FAQ price', related='contract_line.equiv_faq_price', store=True)

    deposit_amount = fields.Float(string='Deposit Amount')

    print_company = fields.Boolean(string='Print Company Name')

    open_qty = fields.Float(string='No Payment Qty')

    list_open_qty = fields.One2many('open.qty.npe', 'purchase_contract_id')

    user_approve = fields.Many2one('res.users', string='User Approve', readonly=False, domain=[('trader', '=', True)])

    percent_advance_price = fields.Integer(string="Percent Advance Price", default=70)
    eudr_check = fields.Boolean(string='Is EUDR', default=False)
    
    @api.onchange("certificate_id", "partner_id", 'eudr_check')
    def onchange_license_id(self):
        # for this in self:
        if self.certificate_id and self.partner_id:
            res = {}
            icheck = [False]
            if self.eudr_check == False :
                icheck = [False]
            else:
                icheck = [False, True]
            res['domain'] = {'license_id': [('partner_id', '=', self.partner_id.id), 
							('certificate_id', '=', self.certificate_id.id), ('state', '=', 'active'), 
                            ('lock_purchase', '=', False), ('parent_id', '=', None), 
                            ('crop_id', '=', self.crop_id.id), ('available_amount','>', 0),
                            ('eudr_check', 'in', icheck)]} 
            # print(res)
            return res
        
class OpenQtyNPE(models.Model):
    _name = 'open.qty.npe'

    purchase_contract_id = fields.Many2one('purchase.contract')
    contract_id = fields.Many2one('purchase.contract', string='NPE')
    qty = fields.Float(string='')
