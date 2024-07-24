# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
import requests
import json
from datetime import datetime
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class AccountJournal(models.Model):
    _inherit = "account.journal"

    is_api = fields.Boolean(
        string="API",
        default=False,
    )
