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
    
    @api.depends('contract_line', 'contract_line.certificate_id')
    def _compute_list_certificate(self):
        if self.contract_line:
            return