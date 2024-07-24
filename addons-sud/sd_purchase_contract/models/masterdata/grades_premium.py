# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class GradePremiumRoot(models.Model):
    _name = 'grade.premium.root'

    name = fields.Char(string='Name', default='Config For Grade Premium')
    effective_date = fields.Date(string='Effective Date')
    end_date = fields.Date(string='End Date')
    grade_premium_line_ids = fields.One2many('grade.premium', 'grade_premium_root_id')
    state = fields.Selection([
        ('run', 'Running'),
        ('stop', 'Stop')
    ], string='State', default='run')

    def action_stop_config(self):
        for record in self:
            record.write({
                'state': 'stop',
                'end_date': datetime.now().date()
            })

    @api.constrains('state')
    def _check_state(self):
        check = self.search([
            ('id', '!=', self.id),
            ('state', '=', 'run')
        ])
        if check:
            raise UserError(_('You have another record that Running for config, please check again and STOP it!'))


class GradePremium(models.Model):
    _name = 'grade.premium'

    grade_premium_root_id = fields.Many2one('grade.premium.root')
    grade_id = fields.Many2one('product.product', string='Grade')
    premium_discount_g2 = fields.Float(string='Premium . Discount vs G2')
    start_effective_date = fields.Date(string='Effective Date')

    @api.constrains('grade_id')
    def _check_grade_id(self):
        check = self.search([
        ]).filtered(
            lambda x: x.id not in [self.ids] and x.grade_id in [self.grade_id.ids]
        )
        if check:
            raise UserError(_('You have another record that config for %s.') % check[0].grade_id.name)