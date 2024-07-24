# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class ProductionAnalysis(models.Model):
    _inherit = 'production.analysis'

    locked = fields.Boolean(string='Locked Batch PnL', default=False)