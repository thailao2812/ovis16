# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class SContract(models.Model):
    _inherit = "s.contract"
    
    
    # 30/11 Thai lao
    license_id = fields.Many2one('ned.certificate.license', string='License Number')
    expired_date = fields.Date(related='license_id.expired_date', store=True)

    # 30/11 Thao Lao
    @api.onchange('license_id')
    def onchange_license_id(self):
        if self.license_id:
            self.certificate_id = self.license_id.certificate_id.id if self.license_id.certificate_id else False
        else:
            self.certificate_id = False
            
            
            