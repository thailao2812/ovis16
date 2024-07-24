# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID


class VisualQuality(models.Model):
    _name = 'visual.quality'

    name = fields.Char(string='Name')