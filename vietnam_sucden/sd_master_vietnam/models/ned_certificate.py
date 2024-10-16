# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

class NedCertificate(models.Model):
    _inherit = 'ned.certificate'

    crop_id = fields.Many2one('ned.crop', string='Crop', required=False)
