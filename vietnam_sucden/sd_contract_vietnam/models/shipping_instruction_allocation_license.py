# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class ShippingInstructionLicenseAllocation(models.Model):
    _inherit = 'shipping.instruction.license.allocation'

    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    date_etd = fields.Date(related='shipping_id.factory_etd', string='ETD Date', store=True)
    certificate_id = fields.Many2one(related='shipping_id.shipping_ids.certificate_id', string='Certificate', store=True)
