# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"


class WizardReportStackMerge(models.TransientModel):
    _name = "wizard.report.stack.merge"

    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')

    def generate_report(self):
        return self.env.ref('sd_inventory_vietnam.report_stack_merge').report_action(self)