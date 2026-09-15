# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID


class PostShipment(models.Model):
    _inherit = 'post.shipment'

    ship_to_id = fields.Many2one('res.partner', string='Ship To', related='shipping_id.ship_to', store=True)
    ship_to_address = fields.Char(string='Ship To Address', related='shipping_id.ship_to_address', store=True)