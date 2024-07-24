# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID


class NedCrop(models.Model):
    _inherit = 'ned.crop'

    fixed_cost = fields.Float(string='Fixed Cost')