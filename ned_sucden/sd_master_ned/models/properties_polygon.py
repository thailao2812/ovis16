# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class PropertiesPolygon(models.Model):
    _name = 'properties.polygon'

    name = fields.Char(string='Name')