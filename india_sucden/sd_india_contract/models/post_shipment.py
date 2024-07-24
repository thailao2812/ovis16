# -*- coding: utf-8 -*-
import math

from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import UserError
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
import time
from datetime import datetime,date, timedelta


class PostShipment(models.Model):
    _inherit = "post.shipment"

    ioc_lot_number = fields.Char(string='IOC Lot Number')
    shipping_bill_no = fields.Char(string='Shipping Bill No')
    shipping_bill_date = fields.Date(string='Shipping Bill Date')
    bl_no = fields.Char(string='BL No', related=False, readonly=False, store=True)
    bl_date = fields.Date(string='BL Date')
    partner_id = fields.Many2one('res.partner', string='Customer', related='shipping_id.partner_id', store=True)
    address = fields.Char(string='Address', compute='compute_address', store=True, readonly=False)
    ship_to = fields.Char(string='Ship To')
    address_ship_to = fields.Char(string='Address')

    @api.depends('partner_id')
    def compute_address(self):
        for record in self:
            record.address = ''
            if record.partner_id:
                street = ', '.join([x for x in (record.partner_id.street, record.partner_id.street2) if x])
                if record.partner_id.district_id:
                    street += ' ' + record.partner_id.district_id.name + ' '
                if record.partner_id.city:
                    street += record.partner_id.city + ' '
                if record.partner_id.state_id:
                    street += record.partner_id.state_id.name
                record.address = street

    def button_load(self):
        if self.nvs_nls_id:
            self.env.cr.execute('''DELETE FROM post_shipment_line WHERE post_id = %s''' % (self.id))

            val = {
                'shipping_id': self.nvs_nls_id.shipping_id and self.nvs_nls_id.shipping_id.id or False
            }
            self.write(val)
            do_ids = self.env['delivery.order'].search([
                ('contract_id', '=', self.nvs_nls_id.id)
            ])
            for rec in do_ids:
                self.env['post.shipment.line'].create({
                    'do_id': rec.id,
                    'post_id': self.id
                })
        return True

    def print_shipping_advise(self):
        return self.env.ref('sd_india_contract.report_shipping_advise_india').report_action(self)

    def print_packing_list(self):
        return self.env.ref('sd_india_contract.report_packing_list_india').report_action(self)