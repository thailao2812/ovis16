# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class IrModel(models.Model):
    _inherit = 'ir.model'

    restful_api = fields.Boolean(
        string='Restful Api',
        default=False,
    )
