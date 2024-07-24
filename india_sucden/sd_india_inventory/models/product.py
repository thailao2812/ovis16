# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    hsn_code = fields.Char(string='HSN Code')
    template_qc = fields.Selection([
        ('raw', 'Raw Coffee'),
        ('clean', 'Clean Coffee'),
        ('c_grade', 'C Grade Coffee'),
        ('pb_grade', 'PB Grade Coffee'),
        ('husk', 'Husk & Process Loss'),
        ('lower', 'Lower Grade'),
        ('bulk', 'Bulk Template'),
        ('clean_bulk', 'Clean Bulk'),
        ('bag', 'Bag')
    ], string='Template for Quality Analysis', required=True)
    default_code = fields.Char(
        'Internal Reference', compute=False,
        inverse=False, store=True, required=True)

    @api.depends('default_code', 'name')
    def _compute_display_wp(self):
        for record in self:
            if record.default_code and record.name:
                record.display_wb = record.default_code + ' ' + record.name
            else:
                record.display_wb = ''

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        res['uom_id'] = self.env.ref('uom.product_uom_kgm').id
        res['uom_po_id'] = self.env.ref('uom.product_uom_kgm').id
        return res

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.user.user_has_groups('sd_india_master.group_admin_india'):
            raise UserError(_("You don't have permission Create Product to do that"))
        res = super().create(vals_list)
        product_variant = self.env['product.product'].search([
            ('product_tmpl_id', '=', res.id)
        ])
        if product_variant:
            product_variant.write({
                'hsn_code': res.hsn_code,
                'template_qc': res.template_qc,
                'default_code': res.default_code
            })
        return res

    def write(self, vals):
        if not self.env.user.user_has_groups('sd_india_master.group_admin_india'):
            raise UserError(_("You don't have permission Write Product to do that"))
        res = super().write(vals)
        product_variant = self.env['product.product'].search([
            ('product_tmpl_id', '=', self.id)
        ])
        if product_variant:
            product_variant.write({
                'hsn_code': self.hsn_code,
                'template_qc': self.template_qc,
                'default_code': self.default_code
            })
        return res

    def unlink(self):
        if not self.env.user.user_has_groups('sd_india_master.group_admin_india'):
            raise UserError(_("You don't have permission Delete Product to do that"))
        return super(ProductTemplate, self).unlink()


class ProductProduct(models.Model):
    _inherit = 'product.product'

    hsn_code = fields.Char(string='HSN Code')
    template_qc = fields.Selection([
        ('raw', 'Raw Coffee'),
        ('clean', 'Clean Coffee'),
        ('c_grade', 'C Grade Coffee'),
        ('pb_grade', 'PB Grade Coffee'),
        ('husk', 'Husk & Process Loss'),
        ('lower', 'Lower Grade'),
        ('bulk', 'Bulk Template'),
        ('clean_bulk', 'Clean Bulk'),
        ('bag', 'Bag')
    ], string='Template for Quality Analysis')

    def name_get(self):
        result = []
        # if self._context.get('delivery_registration'):
        for pro in self:
            result.append((pro.id, pro.default_code + ' ' + pro.name))
        return result

    @api.depends('default_code', 'name')
    def _compute_display_wp(self):
        for record in self:
            if record.default_code and record.name:
                record.display_wb = record.default_code + ' ' + record.name
            else:
                record.display_wb = ''