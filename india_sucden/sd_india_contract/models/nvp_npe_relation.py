# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from datetime import datetime, date, timedelta
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class NVPNPERelation(models.Model):
    _inherit = "npe.nvp.relation"

    note = fields.Text(string='Term and Condition', related="npe_contract_id.note", store=True)
    date_fixed = fields.Date(string='Date Fixed', default=datetime.now())
    contract_date = fields.Date(string='Contract Date', related='contract_id.date_order', store=True)