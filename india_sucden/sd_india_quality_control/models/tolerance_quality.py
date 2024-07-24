# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID


class ToleranceQuality(models.Model):
    _name = 'tolerance.quality'

    product_category_id = fields.Many2one('product.category', string='Grade')
    deduction_quality_id = fields.Many2one('deduction.quality', string='Deduction', domain=[('code', 'in',
                                                                                             ['BB', 'Bleach', 'IDB',
                                                                                              'RB'])])
    tolerance_percent = fields.Float(string='Tolerance %')
    after_deduction = fields.Float(string='After Tolerance Limit Deduction')
