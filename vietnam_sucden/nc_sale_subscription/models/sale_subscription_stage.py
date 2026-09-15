# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class SaleSubscriptionStage(models.Model):
    _inherit = 'sale.subscription.stage'

    template_id = fields.Many2one('sale.subscription.template', string='Proposal Type')
    code = fields.Char(string='Code', size=64)
    on_reject = fields.Boolean('Can be Rejected?', default=False)
    approval_ids = fields.Many2many('res.users', 'stage_approval_rel','stage_id',  \
                                    'user_id', string='Approval Users')


    def write(self, vals):
        if vals.get('sequence'):
            if self.env.uid != 2:
                raise UserError(_('You do not have permission to modify this document.'))
        result = super(SaleSubscriptionStage, self).write(vals)
        return result