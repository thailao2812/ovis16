# -*- coding: utf-8 -*-
import calendar
import datetime
from time import gmtime, strftime
DATE_FORMAT = "%Y-%m-%d"
# from odoo import tools
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class ReportInvoiceWithPayment(models.AbstractModel):
    _name = 'sd_security_gate.template_report_security_gate_qc'
    _description = 'Account report with payment lines'
    
    #
    # def _set_localcontext(self):
    #     localcontext = super(Parser, self)._set_localcontext()
    #
    #
    #     localcontext.update({
    #         'get_grn':self.get_grn,
    #     })
    #     return localcontext
    #
    #
    # @api.model
    # def _get_report_values(self, docids, data=None):
    #     return {
    #         'get_grn':self.get_grn
    #         }
    #
    #
    # @api.model
    # def get_grn(self, obd):
    #
    #     return 'asasasas'