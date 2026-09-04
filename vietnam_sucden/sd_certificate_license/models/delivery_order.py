# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

class DeliveryOrder(models.Model):
    _inherit = "delivery.order"
    
    # certificated_ids = fields.Many2many('ned.certificate', 'delivery_order_certificate_ref', 'delivery_order_id', 'cert_id', string='Certificate List')
    certificated_ids = fields.Many2many(related='contract_id.certificate_id_list', string='Cert. Compliant')
    certificate_list = fields.Char(string='Certificate List', compute='_compute_certificate_list', store=True)
    factory_etd = fields.Date(related='shipping_id.factory_etd', string='Factory ETD')
    
    @api.depends('certificated_ids')
    def _compute_certificate_list(self):
        for record in self:
            certificated_name = False
            if record.certificated_ids:
                certificated_name = '; '.join(i.name for i in record.certificated_ids)
                record.certificate_list = certificated_name
            else:
                record.certificate_list = ''

    # @api.onchange('shipping_id')
    # def _onchange_certificated_ids(self):
    #     if self.shipping_id:
    #         self.certificated_ids = self.shipping_id.certificated_ids
    #     else:
    #         self.certificated_ids = False
