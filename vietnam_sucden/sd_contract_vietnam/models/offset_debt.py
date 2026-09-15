# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class OffsetDebt(models.Model):
    _name = "offset.debt"
    _description = "Offset Debt"

    purchase_contract_id = fields.Many2one('purchase.contract', string="Purchase Contract")
    amount = fields.Float(string="Amount")
    reason = fields.Text(string="Reason")