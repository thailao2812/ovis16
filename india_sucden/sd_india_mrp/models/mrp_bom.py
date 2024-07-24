# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID


class MRPBom(models.Model):
    _inherit = 'mrp.bom'

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, str(rec.code) + ' ' + str(rec.remarks)))
        return result