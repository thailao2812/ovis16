# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError


class Exchange(models.Model):
    _name = 'exchange.india'
    _inherit = ['mail.thread']

    name = fields.Char(string='Exchange')
    default_data = fields.Selection([
        ('no', 'No'),
        ('yes', 'Yes')
    ], string='Default', default='no')
    active = fields.Boolean(string='Active')
    market_id = fields.Many2one('market.india', string='Market')
    currency_id = fields.Many2one('res.currency', string='Currency')
    rate = fields.Float(string='Rate', default=1.00000, digits=(12, 5))
    yield_loss = fields.Float(string='Yield Loss')

    @api.onchange('market_id')
    def onchange_market_id(self):
        if self.market_id:
            self.rate = self.market_id.rate

    @api.constrains('currency_id', 'rate')
    def _check_rate_currency(self):
        if self.currency_id and self.currency_id.name == 'USC':
            if not self.rate or self.rate == 1:
                raise UserError(_("You need to input rate for USC -> USD when you choose USC Currency!!"))