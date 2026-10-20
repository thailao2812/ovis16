# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from datetime import date,datetime, timedelta


class ShippingInstruction(models.Model):
    _inherit = 'shipping.instruction'

    ship_to = fields.Many2one('res.partner', string='Ship To')