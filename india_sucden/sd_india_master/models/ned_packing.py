# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError


class NedPacking(models.Model):
    _inherit = 'ned.packing'

    @api.model
    def create(self, vals):
        if not self.env.user.has_group('sd_india_master.group_edit_ned_packing'):
            raise UserError(_("You don't have permission to do that"))
        return super(NedPacking, self).create(vals)

    def write(self, vals):
        if not self.env.user.has_group('sd_india_master.group_edit_ned_packing'):
            raise UserError(_("You don't have permission to do that"))
        return super(NedPacking, self).write(vals)