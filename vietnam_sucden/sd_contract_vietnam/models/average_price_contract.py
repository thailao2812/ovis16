# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class AveragePriceContract(models.Model):
    _name = 'average.price.contract'

    partner_id = fields.Many2one('res.partner', string='Partner')
    total_un_receive = fields.Float(string='Total Un-Receive')
    average_price = fields.Float(string='Price')