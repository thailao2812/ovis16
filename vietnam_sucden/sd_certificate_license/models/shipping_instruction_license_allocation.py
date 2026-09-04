# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class ShippingInstructionLicenseAllocation(models.Model):
    _inherit = 'shipping.instruction.license.allocation'

    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    date_etd = fields.Date(related='shipping_id.factory_etd', string='ETD Date', store=True)
    shipment_date = fields.Date(related='shipping_id.shipment_date',string='Shipment Date', store=True)
    certificated_ids = fields.Many2many(related='shipping_id.certificated_ids', string='Cer Compliant')
    partner_id = fields.Many2one(related='license_id.partner_id', store=True)
    certificate_id = fields.Many2one(related='license_id.certificate_id', store=True)
    
    @api.onchange('certificated_ids','shipping_id.certificated_ids')
    def _onchange_certificated_ids(self):
        if self.certificated_ids:
            certificated_ids = self.certificated_ids.ids
            licenses = self.env['ned.certificate.license'].search([('certificated_ids', 'in', certificated_ids)])

            # Lọc các record thỏa mãn hoàn toàn điều kiện
            valid_licenses = []
            for license in licenses:
                if set(certificated_ids).issubset(set(license.certificated_ids.ids)):
                    valid_licenses.append(license.id)
            return {
                'domain': {
                    'license_id': [('id', 'in', valid_licenses)]
                }
            }
        else:
            return {
                'domain': {
                    'license_id': []
                }
            }
