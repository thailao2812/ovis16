# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    quality_type = fields.Selection([
        ('wet', 'Wet'),
        ('clean', 'Clean'),
        ('std', 'STD')
    ], string='Quality Type', default=None)

    @api.model
    def create(self, vals):
        if not self.env.user.login == 'tuan.tran@sucden.com' and not self.env.user.login == 'thai.lao@sucden.com' and not self.env.user.login == 'admin':
            raise UserError(_("You don't have permission to do that"))
        res = super(ProductTemplate, self).create(vals)
        product_variant = self.env['product.product'].search([
            ('product_tmpl_id', '=', res.id)
        ])
        if product_variant:
            product_variant.write({
                'quality_type': res.quality_type,
            })
        return res

    def write(self, vals):
        if not self.env.user.login == 'tuan.tran@sucden.com' and not self.env.user.login == 'thai.lao@sucden.com' and not self.env.user.login == 'admin':
            raise UserError(_("You don't have permission to do that"))
        res = super(ProductTemplate, self).write(vals)
        for rec in self:
            product_variant = self.env['product.product'].search([
                ('product_tmpl_id', '=', rec.id)
            ])
            if product_variant:
                product_variant.write({
                    'quality_type': rec.quality_type,
                })
        return res


class ProductProduct(models.Model):
    _inherit = 'product.product'

    quality_type = fields.Selection([
        ('wet', 'Wet'),
        ('clean', 'Clean'),
        ('std', 'STD')
    ], string='Quality Type', default=None)

    @api.model
    def create(self, vals):
        if not self.env.user.login == 'tuan.tran@sucden.com' and not self.env.user.login == 'thai.lao@sucden.com':
            raise UserError(_("You don't have permission to do that"))
        return super(ProductProduct, self).create(vals)

    def write(self, vals):
        if not self.env.user.login == 'tuan.tran@sucden.com' and not self.env.user.login == 'thai.lao@sucden.com':
            raise UserError(_("You don't have permission to do that"))
        return super(ProductProduct, self).write(vals)
