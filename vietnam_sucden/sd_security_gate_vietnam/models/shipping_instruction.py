# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class ShippingInstruction(models.Model):
    _inherit = 'shipping.instruction'

    gate_ids = fields.One2many('ned.security.gate.queue','shipping_id', string='Security Gate Queue')

