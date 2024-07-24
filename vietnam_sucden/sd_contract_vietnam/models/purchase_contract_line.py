# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class PurchaseContractLine(models.Model):
    _inherit = 'purchase.contract.line'

    diff_price = fields.Float(string='Differencial Price', compute=False, store=True, readonly=False)
    delivery_place = fields.Many2one('delivery.place', string='Delivery Place', related='contract_id.delivery_place_id', store=True)
    crop_id = fields.Many2one('ned.crop', string='Crop', related='contract_id.crop_id', store=True)

    equiv_faq_price = fields.Float(string='Equiv. FAQ price')

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