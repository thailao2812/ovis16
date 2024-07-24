# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class DiffConfigurationContract(models.Model):
    _name = 'diff.configuration'

    delivery_place = fields.Many2one('delivery.place', string='Delivery Place')
    product_id = fields.Many2one('product.product', string='Product')
    diff = fields.Float(string='Diff')
    crop_id = fields.Many2one('ned.crop', string='Crop')