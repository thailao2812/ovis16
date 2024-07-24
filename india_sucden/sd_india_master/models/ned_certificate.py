# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError


class NedCertificate(models.Model):
    _inherit = 'ned.certificate'

    sale_premium = fields.Float(string='Sale Premium')
    purchase_premium = fields.Float(string='Purchase Premium')

    @api.model
    def create(self, vals):
        if not self.env.user.user_has_groups('sd_india_master.group_admin_india'):
            raise UserError(_("You don't have permission Create Certificate to do that"))
        return super(NedCertificate, self).create(vals)

    def write(self, vals):
        if not self.env.user.user_has_groups('sd_india_master.group_admin_india'):
            raise UserError(_("You don't have permission Write Certificate to do that"))
        return super(NedCertificate, self).write(vals)

    def unlink(self):
        if not self.env.user.user_has_groups('sd_india_master.group_admin_india'):
            raise UserError(_("You don't have permission Delete Certificate to do that"))
        return super(NedCertificate, self).unlink()
