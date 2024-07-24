# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class AccountPayment(models.Model):
    _inherit = "account.payment"
    _description = "Payments"

    request_date = fields.Date(string='Request Date', related='request_payment_id.date', store=True)