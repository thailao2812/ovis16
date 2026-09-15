# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

class RequestKCSLine(models.Model):
    _inherit="request.kcs.line"

    contract_no = fields.Char(related='picking_id.contract_no', string="Contract no", readonly=True, store=True)
