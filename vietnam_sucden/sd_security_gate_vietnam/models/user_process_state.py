# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class UserProcessState(models.Model):
    _name = 'user.process.state'

    request_payment_id = fields.Many2one('request.payment')
    user_id = fields.Many2one('res.users', string='User')
    date = fields.Datetime(string='Datetime')
    state = fields.Char(string='State')