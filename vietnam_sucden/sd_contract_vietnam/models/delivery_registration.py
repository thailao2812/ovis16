# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class DeliveryRegistration(models.Model):
    _inherit = 'ned.security.gate.queue'

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        delivery_registration = self.search(args + domain, limit=limit)
        if self._context.get('request_payment'):
            try:
                product = self.env['product.product'].browse(self._context.get('product_id'))
                delivery_registration = self.search(args + domain, limit=limit).filtered(
                    lambda x: self._context.get('product_id') in x.product_ids.ids)
            except ValidationError as e:
                raise UserError(_("Invalid field input : %s") % e.args)
            return delivery_registration.name_get()
        return delivery_registration.name_get()
