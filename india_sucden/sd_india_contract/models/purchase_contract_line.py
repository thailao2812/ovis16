# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class PurchaseContractLine(models.Model):
    _inherit = "purchase.contract.line"

    @api.onchange('product_id')
    def product_id_change(self):
        res = super().product_id_change()
        self.name = self.product_id.name
        return res

    @api.depends('product_qty', 'price_unit', 'tax_id', 'contract_id.premium')
    def _compute_amount(self):
        res = super(PurchaseContractLine, self)._compute_amount()
        for line in self:
            line.update({
                'price_subtotal': line.price_subtotal + (line.contract_id.premium * line.product_qty),
            })
        return res