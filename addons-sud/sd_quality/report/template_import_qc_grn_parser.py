# -*- encoding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError
from datetime import datetime
from datetime import date

import time
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%d-%m-%Y"
# -*- encoding: utf-8 -*-


class Parser(models.AbstractModel):
    _name = 'report.report_template_import_qc_grn'
    _inherit = ['report.report_aeroo.abstract']
    _description = 'report.report_template_import_qc_grn'
    
    def _set_localcontext(self):
        localcontext = super(Parser, self)._set_localcontext()
        
        localcontext.update({
        })
        return localcontext
    
    


