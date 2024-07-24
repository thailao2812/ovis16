# -*- coding: utf-8 -*-
import calendar
import datetime
from time import gmtime, strftime
DATE_FORMAT = "%Y-%m-%d"
# from odoo import tools
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class ReportTemplateReportSecurityGate(models.AbstractModel):
    _name = 'sd_security_gate.template_report_security_gate'
    _description = 'template_report_security_gate'