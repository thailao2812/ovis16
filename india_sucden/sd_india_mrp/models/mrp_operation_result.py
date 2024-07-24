# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID


class MrpOperationResult(models.Model):
    _inherit = 'mrp.operation.result'

    production_shift = fields.Selection([
        ('1', 'Shift 1'),
        ('2', 'Shift 2'),
        ('3', 'Shift 3'), ], 'Production Shift', required=True, default="1")