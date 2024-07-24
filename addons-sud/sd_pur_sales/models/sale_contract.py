# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

# -*- coding: utf-8 -*-
from datetime import datetime
from pytz import timezone

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class SaleContract(models.Model):
    _inherit = "sale.contract"
    
    
    def print_printout_nvs(self):
        return self.env.ref(
            'sd_pur_sales.printout_nvs_report').report_action(self)
    
    
    
    

    
    
    
    
