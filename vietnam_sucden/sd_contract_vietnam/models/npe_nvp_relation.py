# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class NPENVPRelation(models.Model):
    _inherit = 'npe.nvp.relation'

    open_qty = fields.Float(string='Open Qty')

