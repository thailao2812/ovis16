# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    quality_slip_no = fields.Char(string='1St Quality Slip No', related='security_gate_id.quality_slip_no', store=True)

    type_contract = fields.Selection([
        ('cr', 'Regular Contract'),
        ('cs', 'Consignment Contract')
    ], string='Type Contract', related='security_gate_id.type_contract', store=True)