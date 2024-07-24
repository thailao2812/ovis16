# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class PostShipMent(models.Model):
    _inherit = "post.shipment"

    security_gate_id = fields.Many2one('ned.security.gate.queue','Security Gate')
    