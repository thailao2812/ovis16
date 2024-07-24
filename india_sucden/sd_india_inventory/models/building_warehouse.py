# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID


class BuildingWarehouse(models.Model):
    _name = 'building.warehouse'
    _inherit = ['mail.thread']
    _order = 'create_date desc, id desc'

    name = fields.Char(string='Name of building', required=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=True)
