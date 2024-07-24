# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class ResUsers(models.Model):
    _inherit = 'res.users'

    create_partner = fields.Boolean(string='Create Partner')
