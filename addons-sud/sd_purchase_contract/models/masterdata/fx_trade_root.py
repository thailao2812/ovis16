# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression



class AccountIncoterms(models.Model):
    _inherit = "account.incoterms"
    _description = 'Account Incoterms'
    
    def name_get(self):
        result = []
        for pro in self:
            result.append((pro.id, pro.code))
        return result
    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            args += ['|',('name', operator, name),('code',operator, name)]
        district = self.with_context(from_name_search=True).search(args, limit=limit)
        return district.name_get()

class FX_trade_root(models.Model):
    _name = 'fx.trade.root'

    name = fields.Char(string='Name', default="Config for FX")
    effective_date = fields.Date(string='Effective Date')
    end_date = fields.Date(string='End Date')
    fx_trade_line_ids = fields.One2many('fx.trade', 'fx_trade_root_id')
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


class FX(models.Model):
    _name = 'fx.trade'

    fx_trade_root_id = fields.Many2one('fx.trade.root')
    location_id = fields.Many2one('delivery.place', string="Location")
    name = fields.Char(string='Name')
    delivery_team_id = fields.Many2one('account.incoterms', string='Delivery Term')
    t_cost_factory = fields.Float(string='T-cost to factory')
    start_effective_date = fields.Date(string='Effective Date')

    @api.constrains('location_id')
    def _check_location_id(self):
        check = self.search([
        ]).filtered(
            lambda x: x.id not in [self.ids] and x.location_id in [self.location_id.ids]
                      and x.fx_trade_root_id == self.fx_trade_root_id.id
        )
        if check:
            raise UserError(_('You have another record that config for %s. '
                              'Please choose another location.') % check[0].location_id.name)
    