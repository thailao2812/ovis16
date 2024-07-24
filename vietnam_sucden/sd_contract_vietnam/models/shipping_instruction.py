# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class ShippingInstruction(models.Model):
    _inherit = 'shipping.instruction'

    process_state = fields.Selection([
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed')
    ], string="Progress State", default=None)

    @api.model
    def create(self, vals):
        if not self.user_has_groups('sd_contract_vietnam.group_full_right_shipping_instruction'):
            raise UserError(_("You don't have permission to do that"))
        return super(ShippingInstruction, self).create(vals)

    def write(self, vals):
        if not self.user_has_groups('sd_contract_vietnam.group_full_right_shipping_instruction'):
            raise UserError(_("You don't have permission to do that"))
        return super(ShippingInstruction, self).write(vals)
