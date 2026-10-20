# -*- coding: utf-8 -*-
from odoo import fields, models

class HrEmployeePrivate(models.Model):
    _inherit = 'hr.employee'

    is_manager = fields.Boolean('Is manager')