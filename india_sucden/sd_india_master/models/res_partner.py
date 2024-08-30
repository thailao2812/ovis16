# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    pan_number = fields.Char(string='Pan Number')
    ifsc_code = fields.Char(string='IFSC Code')
    agent = fields.Boolean(string='Agent')
    shipping_customer = fields.Boolean(string='Shipping Customer')
    forwarding_agent_check = fields.Boolean(string='Forwarding Agent')
    estate_name = fields.Char(string='Estate Name')
    # accounting_type = fields.Selection([
    #     ('coffee_export', 'Coffee Export'),
    #     ('coffee_local', 'Coffee Local'),
    #     ('expense', 'Expense')
    # ], string='Accounting Type', required=False)

    @api.model
    def create(self, vals):
        if not self.env.user.user_has_groups('sd_india_master.group_admin_india'):
            raise UserError(_("You don't have permission Create Contact to do that"))
        return super(ResPartner, self).create(vals)

    def write(self, vals):
        if not self.env.user.user_has_groups('sd_india_master.group_admin_india'):
            raise UserError(_("You don't have permission Write Contact to do that"))
        return super(ResPartner, self).write(vals)

    def unlink(self):
        if not self.env.user.user_has_groups('sd_india_master.group_admin_india'):
            raise UserError(_("You don't have permission Delete Contact to do that"))
        return super(ResPartner, self).unlink()