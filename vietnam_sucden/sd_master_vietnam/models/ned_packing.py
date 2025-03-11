# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class NedPacking(models.Model):
    _inherit = 'ned.packing'

    @api.model
    def create(self, vals):
        if not self.env.user.login == 'tuan.tran@sucden.com' and not self.env.user.login == 'thai.lao@sucden.com' and not self.env.user.login == 'admin':
            raise UserError(_("You don't have permission to do that"))
        return super(NedPacking, self).create(vals)

    def write(self, vals):
        if not self.env.user.login == 'tuan.tran@sucden.com' and not self.env.user.login == 'thai.lao@sucden.com' and not self.env.user.login == 'admin':
            raise UserError(_("You don't have permission to do that"))
        return super(NedPacking, self).write(vals)
