# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID


class ResDistrict(models.Model):
    _inherit = 'res.district'

    location = fields.Boolean(string='Is Location?', default=False)
