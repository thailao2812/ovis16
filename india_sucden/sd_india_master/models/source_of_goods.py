# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import UserError


class SourceOfGoods(models.Model):
    _name = 'source.goods'

    district_id = fields.Many2one('res.district', string='District')
    name = fields.Char(string='Name')
    active = fields.Boolean(string='Active', default=True)
