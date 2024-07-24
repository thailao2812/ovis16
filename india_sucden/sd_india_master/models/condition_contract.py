# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import UserError


class ConditionContract(models.Model):
    _name = 'condition.contract'

    display_name = fields.Char(string='Description', default='Tolerance Limit')
    name = fields.Float(string='Condition')
    active = fields.Boolean(string='Active', default=True)

    @api.constrains('active')
    def constrain_active(self):
        for record in self:
            if record.active:
                check_constraint = self.search([
                    ('id', '!=', record.id),
                    ('active', '=', True)
                ])
                if check_constraint:
                    raise UserError(_("You can't active more than one rule for contract!"))