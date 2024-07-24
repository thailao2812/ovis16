# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class CostFOB(models.Model):
    _name = 'fob.value'

    effective_date = fields.Date(string='Effective Date')
    end_date = fields.Date(string='End Date')
    name = fields.Char(string='Name', default='Configuration FOB')
    cost_fob_lines = fields.One2many('cost.fob', 'fob_value_id')
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
    def constrains_for_fob(self):
        check = self.search([
            ('state', '=', 'run'),
            ('id', '!=', self.id)
        ])
        if check:
            raise UserError(_('You have another record that Running for config, please check again and STOP it!'))


class ConditionCostFOB(models.Model):
    _name = 'cost.fob'

    fob_value_id = fields.Many2one('fob.value')
    type = fields.Selection([
        ('faq', 'FAQ'),
        ('grade', 'Grade')
    ], string='Type Cost FOB HCM', default=None)
    product_id = fields.Many2one('product.product', string='Grade')
    partner_code = fields.Char(string='Source')
    delivery_to_location = fields.Many2one('delivery.place', string='Delivery To Location')
    diff_delivery_to_location = fields.Char(string='# Location', compute='_compute_diff_location', store=True)
    cost_fob_hcm = fields.Float(string='Cost to FOB HCM')

    @api.depends('product_id', 'delivery_to_location')
    def _compute_diff_location(self):
        for record in self:
            if record.product_id:
                record.diff_delivery_to_location = ''
            else:
                if record.delivery_to_location:
                    record.diff_delivery_to_location = ''
                else:
                    record.diff_delivery_to_location = 'Different'
