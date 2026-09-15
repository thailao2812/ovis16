# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import UserError
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class DeliveryPlace(models.Model):
    _inherit = "delivery.place"

    warehouse_id = fields.Many2one('stock.warehouse',)