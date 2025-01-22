# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import UserError


class GradePremium(models.Model):
    _name = 'grade.premium.india'
    _description = 'Grade Premium'

    name = fields.Char(string='Name', required=True)
    crop_id = fields.Many2one('ned.crop', string='Crop Season', required=True)
    product_ids = fields.Many2many('product.product', string='Items', required=True)
    premium = fields.Float(string='Grade Premium (+/-)', required=True)