# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID


class DeductionLine(models.Model):
    _inherit = 'deduction.line'

    security_gate_id = fields.Many2one('ned.security.gate.queue')