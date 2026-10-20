# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class WizardInvoiceLine(models.TransientModel):
    _inherit = "wizard.invoice.line"

    price_unit = fields.Float(string='Price Unit', digits=(12, 4))