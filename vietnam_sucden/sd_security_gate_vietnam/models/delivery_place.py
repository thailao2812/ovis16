# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from datetime import datetime, date, timedelta


class DeliveryPlace(models.Model):
    _inherit = 'delivery.place'

    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')