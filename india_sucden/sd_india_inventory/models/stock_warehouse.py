# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    def name_get(self):
        res = []
        for record in self:
            res.append((record.id, record.name + ' - ' + record.code))
        return res

