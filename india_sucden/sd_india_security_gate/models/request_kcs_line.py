# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID


class RequestKCSLine(models.Model):
    _inherit = 'request.kcs.line'

    quality_slip_no = fields.Char(string='1St Quality Slip No', related='picking_id.quality_slip_no', store=True)
    dr_number = fields.Many2one('ned.security.gate.queue', string='DR number', related='picking_id.security_gate_id', store=True)
    vehicle_no = fields.Char(string='Vehicle No', related='picking_id.vehicle_no', store=True)