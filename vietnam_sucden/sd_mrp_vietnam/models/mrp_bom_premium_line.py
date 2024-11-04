# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID


class MRPBomPremiumLine(models.Model):
    _inherit = 'mrp.bom.premium.line'

    black_broken = fields.Float(string='Black Broken')
    defect = fields.Float(string='Defect')