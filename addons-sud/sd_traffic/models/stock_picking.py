# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    x_inspectator = fields.Many2one('x_inspectors.kcs', related='kcs_line.x_inspectator')
