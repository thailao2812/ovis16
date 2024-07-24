# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class PtbfFixPrice(models.Model):
    _inherit = "ptbf.fixprice"

    contract_p_id = fields.Many2one('s.contract', string="PNo")