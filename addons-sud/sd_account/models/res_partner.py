# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"

class ResPartner(models.Model):
    _inherit = "res.partner"
    
    property_vendor_advance_acc_id = fields.Many2one('account.account', 
        string="Vendor advance account", 
        domain="[('account_type', '=', 'liability_payable'),('deprecated', '=', False)]",
        required=False)
    
    
    property_customer_advance_acc_id = fields.Many2one('account.account', 
        string="Customer advance account", 
        domain="[('account_type', '=', 'asset_receivable'), ('deprecated', '=', False)]",
        required=False)
    
    property_account_payable_id = fields.Many2one('account.account', 
        string="Account Payable",
        domain="[('account_type', '=', 'liability_payable'), ('deprecated', '=', False), ('company_id', '=', current_company_id)]",
        help="This account will be used instead of the default one as the payable account for the current partner",
        required=True)
    property_account_receivable_id = fields.Many2one('account.account', 
        string="Account Receivable",
        domain="[('account_type', '=', 'asset_receivable'), ('deprecated', '=', False), ('company_id', '=', current_company_id)]",
        help="This account will be used instead of the default one as the receivable account for the current partner",
        required=True)
    
    
    @api.constrains('vat', 'country_id')
    def check_vat(self):
        # The context key 'no_vat_validation' allows you to store/set a VAT number without doing validations.
        # This is for API pushes from external platforms where you have no control over VAT numbers.
        if self.env.context.get('no_vat_validation'):
            return
        
        return

        for partner in self:
            country = partner.commercial_partner_id.country_id
            if partner.vat and self._run_vat_test(partner.vat, country, partner.is_company) is False:
                partner_label = _("partner [%s]", partner.name)
                msg = partner._build_vat_error_message(country and country.code.lower() or None, partner.vat, partner_label)
                raise ValidationError(msg)
    
    
    