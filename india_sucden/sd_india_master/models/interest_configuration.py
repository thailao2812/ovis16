# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import UserError


class InterestConfiguration(models.Model):
    _name = 'interest.configuration'

    name = fields.Many2one('ned.crop', string='Season')
    number_of_day = fields.Integer(string='Number of Day Without Interest')
    state = fields.Selection([
        ('new', 'New'),
        ('approve', 'Approve')
    ], string='State', default='new')

    def button_approve(self):
        for rec in self:
            rec.state = 'approve'

    def button_set_draft(self):
        for rec in self:
            rec.state = 'new'

    @api.constrains('name', 'state')
    def check_constrains_interest(self):
        for record in self:
            checking = self.env['interest.configuration'].search([
                ('name', '=', record.name.id),
                ('state', '=', 'approve'),
                ('id', '!=', record.id)
            ])
            if checking:
                raise UserError(_("You cannot have double record for 1 Season!"))
