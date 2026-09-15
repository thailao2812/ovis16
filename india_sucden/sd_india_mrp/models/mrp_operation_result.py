# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError


class MrpOperationResult(models.Model):
    _inherit = 'mrp.operation.result'

    production_shift = fields.Selection([
        ('1', 'Shift 1'),
        ('2', 'Shift 2'),
        ('3', 'Shift 3'), ], 'Production Shift', required=True, default="1")

    def button_confirm(self):
        for rec in self:
            for i in rec.produced_products:
                if not i.picking_id:
                    raise UserError(_("You cannot Confirm If you've not created GRP for that Production Result"))
            if not any(rec.produced_products.filtered(lambda x: x.state == 'done')):
                raise UserError(_("You cannot Confirm If you've not produced any Product"))
            rec.state = 'done'

    def button_cancel(self):
        for rec in self:
            for i in rec.produced_products:
                if i.state != 'cancel':
                    raise UserError(_("You cannot cancel Production Result which have line is not Cancelled"))
            rec.state = 'cancel'