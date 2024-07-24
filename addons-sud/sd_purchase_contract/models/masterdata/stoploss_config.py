# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class StopLossConfig(models.Model):
    _name = 'stoploss.config'

    name = fields.Char(string='Name', default='Configuration For Stoploss')
    effective_date = fields.Date(string='Effective Date')
    end_date = fields.Date(string='End Date')
    stoploss_line_ids = fields.One2many('stoploss.line', 'stop_loss_config_id')
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
    def constrains_for_stoploss(self):
        check = self.search([
            ('state', '=', 'run'),
            ('id', '!=', self.id)
        ])
        if check:
            raise UserError(_('You have another record that Running for config, please check again and STOP it!'))


class StopLossLine(models.Model):
    _name = 'stoploss.line'

    # stoploss_config_id = fields.Many2one('stoploss.config')
    stop_loss_config_id = fields.Many2one('stoploss.config')
    price = fields.Float(string='Price')
    effective_date = fields.Date(string='Effective Date')