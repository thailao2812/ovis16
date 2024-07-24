from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta


class PSSSent(models.Model):
    _inherit = "pss.sent"

    def choose_date_approve(self):
        for record in self:
            if record.t_contract_id:
                record.t_contract_id.pss_approved_date = record.aproved_date or False
