
# -*- coding: utf-8 -*-

import time
from datetime import datetime
# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict
import re
DATE_FORMAT = "%Y-%m-%d"

class WizradShipmentReport(models.TransientModel):
    _name = "wizard.shipment.report"
    
    date_from = fields.Date(string="Date from")
    date_to = fields.Date(string="Date to")
    
    
    def print_report(self, cr, uid, ids, context=None): 
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'wizard.shipment.report'
        datas['form'] = self.read(cr, uid, ids)[0]
        return {'type': 'ir.actions.report.xml', 'report_name': 'shipment_report' , 'datas': datas}
    
    