# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import UserError


class DocumentContract(models.Model):
    _name = 'document.contract'

    name = fields.Char(string='Name')
