# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class NPENVPRelation(models.Model):
    _inherit = 'npe.nvp.relation'

    open_qty = fields.Float(string='Open Qty')
    request_payment_id = fields.Many2one('request.payment', string='Request Payment')
    remain_request_payment = fields.Float(string='Remain Request Payment', related='request_payment_id.remain_fix_qty', store=True)

