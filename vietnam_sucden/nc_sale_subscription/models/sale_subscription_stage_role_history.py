
# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SaleSubscriptionStageRoleHistory(models.Model):
    _name = 'sale.subscription.stage.role.history'

    @api.onchange('stage_id')
    def _onchange_stage(self):
        if self.stage_id:
            self.name = self.stage_id.name

    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id

    name = fields.Text(string='Comment')
    appr_time = fields.Datetime(string='Action Date')
    appr_by = fields.Many2one('res.users', string="Action By")
    version = fields.Char(string='Version', size=16, default='1')
    sub_id = fields.Many2one('sale.subscription', string='Subscription')
    stage_id = fields.Many2one('sale.subscription.stage', string='Stage')
    role_id = fields.Many2one('sale.subscription.stage.role', 'Role')
    amount_limit = fields.Monetary('Limit Budget', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', 'Currency', default=_default_currency)
    state = fields.Selection([
                              ('send', 'Send'), 
                              ('appr', 'Approve'), 
                              ('submit', 'Submit'), 
                              ('review', 'Review'), 
                              ('revert', 'Revert'),
                              ('assign', 'Assign'),
                              ('reject', 'Reject'),
                              ('comment', 'Comment'),
                            ], string='Action')
    is_revert = fields.Boolean(string='Is Reverted')
    is_bypass = fields.Boolean(string='Is Bypass')