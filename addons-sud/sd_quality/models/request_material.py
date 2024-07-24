# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from datetime import datetime
    
class RequestMaterialsLine(models.Model):
    _inherit = "request.materials.line"
    
    
    packing_id = fields.Many2one('ned.packing', related="stack_id.packing_id",string="Packing", store = True)

    def unlink(self):
        for rec in self:
            if rec.basis_qty > 0:
                raise UserError(_("You cannot delete the line that already created GIP"))
        res = super(RequestMaterialsLine, self).unlink()
        return res
