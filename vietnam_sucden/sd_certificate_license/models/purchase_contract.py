# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class PurchaseContract(models.Model):
    _inherit = 'purchase.contract'

    certificated_ids = fields.Many2many('ned.certificate', 'purchase_contract_ned_certificate_rel', 'purchase_contract_id', 'certificate_id', string="Cer Compliant")
    
    @api.onchange('partner_id', 'license_id')
    def onchange_license_id(self):
        if self.partner_id and self.license_id:
            self.certificated_ids = self.license_id.certificated_ids
            # if self.certificated_ids:
            #     self.premium = sum(self.certificated_ids.mapped('premium'))
        else:
            self.certificated_ids = False
            