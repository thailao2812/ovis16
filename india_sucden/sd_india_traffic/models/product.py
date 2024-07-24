# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError


class ProductProduct(models.Model):
    _inherit = 'product.product'

    item_group_id = fields.Many2one('product.group', string='Item Group')


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    item_group_id = fields.Many2one('product.group', string='Item Group')

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        product_variant = self.env['product.product'].search([
            ('product_tmpl_id', '=', res.id)
        ])
        if product_variant:
            if res.item_group_id:
                product_variant.write({
                    'item_group_id': res.item_group_id.id,
                })
        return res

    def write(self, vals):
        res = super().write(vals)
        product_variant = self.env['product.product'].search([
            ('product_tmpl_id', '=', self.id)
        ])
        if product_variant:
            if self.item_group_id:
                product_variant.write({
                    'item_group_id': self.item_group_id.id
                })
        return res