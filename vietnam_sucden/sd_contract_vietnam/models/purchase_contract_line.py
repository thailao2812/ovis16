# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class PurchaseContractLine(models.Model):
    _inherit = 'purchase.contract.line'

    def _default_vat_in(self):
        return self.env['account.tax'].search([('type_tax_use', '=', 'purchase'), ('default', '=', True)], limit=1)

    diff_price = fields.Float(string='Differencial Price', compute=False, store=True, readonly=False)
    delivery_place = fields.Many2one('delivery.place', string='Delivery Place', related='contract_id.delivery_place_id', store=True)
    crop_id = fields.Many2one('ned.crop', string='Crop', related='contract_id.crop_id', store=True)

    equiv_faq_price = fields.Float(string='Equiv. FAQ price')
    vat_id = fields.Many2one('account.tax', string='VAT', default=_default_vat_in)

    @api.depends('product_qty', 'price_unit', 'tax_id', 'vat_id')
    def _compute_amount(self):
        for line in self:
            price = line.price_unit
            taxes = line.vat_id.compute_all(price, line.contract_id.currency_id, line.product_qty,
                                            product=line.product_id, partner=line.contract_id.partner_id)
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    @api.depends('contract_id', 'crop_id', 'delivery_place', 'difams', 'product_id')
    def compute_diff_price(self):
        for record in self:
            if record.product_id:
                condition = self.env['diff.configuration'].search([
                    ('product_id', '=', record.product_id.id),
                    ('delivery_place', '=', record.delivery_place.id),
                    ('crop_id', '=', record.crop_id.id)
                ], limit=1)
                if condition:
                    record.diff_price = record.difams - condition.diff
                else:
                    record.diff_price = 0
            else:
                record.diff_price = 0