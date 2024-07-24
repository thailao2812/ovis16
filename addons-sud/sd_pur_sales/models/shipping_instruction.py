# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class ShippingInstruction(models.Model):
    _inherit = "shipping.instruction"
    
    
    license_allocation_ids = fields.One2many('shipping.instruction.license.allocation', 'shipping_id',
                                             string='License Allocations')
    license_list = fields.Char(string='License List', compute='_compute_license', store=True)

    @api.depends('license_allocation_ids', 'license_allocation_ids.license_id')
    def _compute_license(self):
        for record in self:
            license_name = False
            if record.license_allocation_ids:
                license_name = '; '.join(i.license_id.name for i in record.license_allocation_ids.filtered(
                    lambda x: x.license_id.name))
                record.license_list = license_name
            else:
                record.license_list = ''
    
    # @api.depends('license_allocation_ids', 'license_allocation_ids.license_id')
    # def _compute_license(self):
    #     for record in self:
    #         if record.license_allocation_ids:
    #             record.license_list = '; '.join(i.license_id.name for i in record.license_allocation_ids)
    #         else:
    #             record.license_list = ''
                
    
    def print_commercial_invoice(self):
        return self.env.ref(
            'sd_pur_sales.report_commercial_invoice').report_action(self)