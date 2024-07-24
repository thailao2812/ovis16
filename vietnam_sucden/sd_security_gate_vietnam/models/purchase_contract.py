
# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
import math
from datetime import datetime, date, timedelta
import math


class PurchaseContract(models.Model):
    _inherit = 'purchase.contract'

    code_partner = fields.Char(string='Partner Code', related='partner_id.partner_code', store=True)
    stop_loss_price = fields.Float(string='Stop Loss %')
    date_fix_for_advance = fields.Integer(string='Time Fix')