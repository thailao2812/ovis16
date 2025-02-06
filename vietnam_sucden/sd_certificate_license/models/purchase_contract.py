# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class PurchaseContract(models.Model):
    _inherit = 'purchase.contract'

    certificated_ids = fields.Many2many('ned.certificate', string="Cer Compliant")
    certificate_list = fields.Char(string='Certificate List', compute='_compute_certificate', store=True)
            
    @api.onchange('partner_id', 'license_id')
    def onchange_license_id(self):
        if self.partner_id and self.license_id:
            self.certificated_ids = self.license_id.certificated_ids
            self.certificate_id = self.license_id.certificate_id.id
        else:
            self.certificated_ids = None
            self.certificate_id = None

    @api.depends('certificated_ids')
    def _compute_certificate(self):
        for record in self:
            certificated_name = False
            if record.certificated_ids:
                certificated_name = '; '.join(i.name for i in record.certificated_ids)
                record.certificate_list = certificated_name
            else:
                record.certificate_list = ''
            
    # @api.depends('license_id')
    # def _compute_certificated_ids(self):
    #     for record in self:
    #         if record.license_id:
    #             record.certificated_ids = [(4, record.license_id.certificate_id.id)]
    #         else:
    #             record.certificated_ids = [(5, 0, 0)]
