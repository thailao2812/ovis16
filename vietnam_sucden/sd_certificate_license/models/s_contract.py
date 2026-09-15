# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

class SContract(models.Model):
    _inherit = 's.contract'

    certificated_ids = fields.Many2many('ned.certificate', 'certificate_s_contract', 's_contract_id', 'certificate_id', string="Cer Compliant", readonly=False)
    # cer_license_type = fields.Selection([('sucden_coffee_license', 'Sucden Coffee License'),
    #                            ('independent_license', '3rd Party License'),
    #                            ], string='Certificate Type') # Guatemala
    certificate_list = fields.Char(string='Certificate List', compute='_compute_certificate', store=True)
    
    @api.depends('contract_line', 'contract_line.certificate_id')
    def _compute_list_certificate(self):
        if self.contract_line:
            return

    @api.depends('certificated_ids', 'certificate_id')
    def _compute_certificate(self):
        for record in self:
            certificated_name = False
            if record.certificated_ids:
                certificated_name = '; '.join(i.name for i in record.certificated_ids)
                record.certificate_list = certificated_name
            elif record.certificate_id:
                certificated_name = record.certificate_id.name
                record.certificate_list = certificated_name
            else:
                record.certificate_list = ''
