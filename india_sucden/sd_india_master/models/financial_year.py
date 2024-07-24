# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import UserError


class FinancialYear(models.Model):
    _name = 'financial.year'

    name = fields.Char(string='Name')
    from_date = fields.Date(string='From')
    to_date = fields.Date(string='To')
    max_value = fields.Float(string='Max Value')
    percent_for_pan = fields.Float(string="Percent with Pan Number")
    percent_unpan = fields.Float(string='Percent without Pan Number')
    state = fields.Selection([
        ('new', 'New'),
        ('confirm', 'Confirm')
    ], string='State', default='new')

    def confirm_year(self):
        for rec in self:
            rec.state = 'confirm'

    def button_set_to_draft(self):
        for rec in self:
            rec.state = 'new'
