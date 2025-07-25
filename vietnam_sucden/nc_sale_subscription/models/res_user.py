# -*- coding: utf-8 -*-
from odoo import fields, models
from odoo.exceptions import UserError

class ResUsers(models.Model):
    _inherit = 'res.users'

    sub_stage_id = fields.Many2one('sale.subscription.stage', 'Subscription Stage')

class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    def unlink(self):
        for rc in self:
            if rc.res_model == 'sale.subscription' and rc.res_id:
                stage_id = self.env['sale.subscription'].browse(rc.res_id).stage_id
                stage_id = stage_id and stage_id.id or 0
                if stage_id != 1:
                    raise UserError('You cannot delete a document that is in stage not draft!')
        return super(IrAttachment, self).unlink()
