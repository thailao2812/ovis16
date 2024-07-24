# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import requests
import json


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    is_api = fields.Boolean(
        string="API",
        default=False,
    )
