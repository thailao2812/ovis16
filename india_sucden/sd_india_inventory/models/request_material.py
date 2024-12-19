# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError


class RequestMaterial(models.Model):
    _inherit = 'request.materials'

    def button_cancel(self):
        for rec in self:
            for i in rec.request_line:
                if i.state != 'cancel':
                    raise UserError(_("You cannot cancel Request Materials which have line is not Cancelled"))
            rec.state = 'cancel'