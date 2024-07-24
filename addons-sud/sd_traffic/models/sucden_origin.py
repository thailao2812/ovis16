# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError


class SucdenOrigin(models.Model):
    _name = "ned.origin"

    name = fields.Char('Name', size=256)
    code = fields.Char('Code', size=128)
