# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class ShippingInstructionLicenseAllocation(models.Model):
    _name = 'shipping.instruction.license.allocation'
    _description = 'Shipping Instruction License Allocation'

    shipping_id = fields.Many2one('shipping.instruction', string='SI No.')
    license_id = fields.Many2one('ned.certificate.license', string='License')
    product_id = fields.Many2one(related='shipping_id.product_id', string='Product')
    grade_id = fields.Many2one('product.category', string='Grade', related='product_id.categ_id', store=True)
    state = fields.Selection(related='shipping_id.state', string='State', store=True)
    allocation_qty = fields.Float('Allocation Qty', digits=(12, 0))
    type = fields.Selection(related='license_id.type', store=True, string='Type')

    crop_id = fields.Many2one(string='Crop', related="shipping_id.crop_id", store = True)

    @api.onchange("product_id", 'shipping_id.certificate_id')
    def onchange_list_license(self):
        res = {}
        if self.product_id:
            cer_list = self.env['ned.certificate.license'].search([('cert_combine.id','=',self.shipping_id.certificate_id.id)])
            res['domain'] = {'license_id': [('id','in',[x.id for x in cer_list])]} 
            return res

    @api.constrains('allocation_qty')
    def _check_allocation_qty(self):
        for i in self:
            if i.allocation_qty <= 0:
                raise ValidationError(_('The allocated quantity must be greater than 0'))


