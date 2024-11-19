# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

class DeliveryOrder(models.Model):
    _inherit = "delivery.order"
    
    certificated_ids = fields.Many2many('ned.certificate', 'delivery_order_certificate_ref', 'delivery_order_id', 'cert_id', string='Certificate List')
    
    @api.onchange('shipping_id')
    def _onchange_certificated_ids(self):
        if self.shipping_id:
            self.certificated_ids = self.shipping_id.certificated_ids
        else:
            self.certificated_ids = False
