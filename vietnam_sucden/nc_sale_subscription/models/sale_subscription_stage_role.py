# -*- coding: utf-8 -*-
from odoo import api, fields, models

class SaleSubscriptionStageRole(models.Model):
    _name = 'sale.subscription.stage.role'

    @api.onchange('stage_id')
    def _onchange_stage(self):
        if self.stage_id:
            self.name = self.stage_id.name

    @api.onchange('approval_ids')
    def _onchange_approval_user(self):
        if self.approval_ids:
            self.appr_num = len(self.approval_ids)

    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id

    @api.depends('history_id')
    def get_need2rev(self):
        pass

    @api.depends('history_id')
    def get_need2app(self):
        for record in self:
            if record.history_id and record.approval_ids:
                lst_user = [appu.id for appu in record.approval_ids]
                app_user = []
                for h in record.history_id:
                    if h.appr_by.id in lst_user and h.version == record.sub_id.version:
                        app_user.append(h.appr_by.id)
                app_user = list(set(app_user))
                tmp = record.appr_num - len(app_user)
                tmp = tmp >= 0 and tmp or 0
                record.need_appr = tmp
            else:
                record.need_appr = record.appr_num

    # sla = fields.Boolean(string='SLA')
    name = fields.Char(string='Comment', size=256)
    # escalation = fields.Boolean(string='Escalation')
    sequence = fields.Char(string='Sequence', size=256)
    alert_time = fields.Integer(string='Day(s) to Approved')
    appr_time = fields.Datetime(string='Approved Date')
    appr_num = fields.Integer(string='Approval Numbers')
    appr_man = fields.Many2one('res.users', string="Approval Main")
    appr_by = fields.Many2one('res.users', string="Approved By")
    sub_id = fields.Many2one('sale.subscription', string='Subscription')
    stage_id = fields.Many2one('sale.subscription.stage', string='Stage')
    amount_limit = fields.Monetary('Limit Budget', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', 'Currency', default=_default_currency)
    history_id = fields.One2many('sale.subscription.stage.role.history', 'role_id', string='History')
    # need_appr = fields.Integer(string='Need to Approve', compute=get_need2app)
    # need_rev = fields.Integer(string='Need to Revert', compute=get_need2rev)
    rev_num = fields.Integer(string='Revert Numbers')
    rev_man = fields.Many2one('res.users', string="Revert Main")
    approval_ids = fields.Many2many('res.users', 'stage_role_approval_rel','role_id',  \
                                    'user_id', string='Approval Users')
    state = fields.Selection([('open', 'Open'), 
                              ('pending', 'Pending'), 
                              ('expired', 'Expired'), 
                              ('done', 'Done')], string='Status', default='open')
    auto_approval = fields.Boolean(string='Auto Approval')

