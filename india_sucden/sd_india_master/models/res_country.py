# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID


class ResCountry(models.Model):
    _inherit = 'res.country'

    def name_get(self):
        result = []
        for pro in self:
            result.append((pro.id, pro.code + ' ' + pro.name))
        return result
