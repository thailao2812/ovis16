# -*- coding: utf-8 -*-
from datetime import datetime, date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.misc import format_date, format_datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import pytz

# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.tools.safe_eval import safe_eval


class Users(models.Model):
    _inherit = "res.users"
    
    
    trader = fields.Boolean(string="Trader")
