# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID


class StockZone(models.Model):
    _inherit = 'stock.zone'

    building_id = fields.Many2one('building.warehouse', string='Building')