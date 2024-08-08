# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class NedCertificateLicense(models.Model):
    _inherit = "ned.certificate.license"

    estate_name = fields.Char(string='Estate Name', related='partner_id.estate_name', store=True)

    @api.depends('stock_allocation_ids.contract_id')
    def _compute_allocated_purchase_contract_ids(self):
        for license in self:
            allocated_purchase_contract_ids = license.purchase_contract_ids.filtered(
                lambda contract: contract.type == 'purchase'
                                 or (contract.type == 'ptbf')
                                 or (contract.type == 'consign') and contract.qty_unfixed > 0
            )
            license.allocated_purchase_contract_ids = allocated_purchase_contract_ids