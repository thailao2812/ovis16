# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from datetime import datetime
    
class VesselRegistration(models.Model):
    _name = 'vessel.registration'

    name = fields.Char(string='Name')
    do_date = fields.Date(string='DO Date')
    status = fields.Selection([
        ('pending', 'Pending'),
        ('done', 'Done')
    ], string='Status', default='pending')
    registration_date = fields.Date(string='Registration Date')
    shipping_instruction = fields.Many2one('shipping.instruction', string='SI No.')
    closing_time = fields.Datetime(string='Closing Time', related='shipping_instruction.closing_time', store=True)
    product_id = fields.Many2one('product.product', string='Product', related='shipping_instruction.product_id',
                                 store=True)
    si_qty = fields.Float(string='SI Qty', related='shipping_instruction.total_line_qty', store=True)
    delivery_place = fields.Many2one('delivery.place', string='Delivery Place',
                                     related='shipping_instruction.delivery_place_id', store=True)
    from_warehouse = fields.Many2one('stock.warehouse', string='From Warehouse')
    booking_no = fields.Char(string='Booking No.', related='shipping_instruction.booking_ref_no', store=True)
    shipping_line = fields.Many2one('shipping.line', string='Shipping Line',
                                    related='shipping_instruction.shipping_line_id', store=True)
    custom_declaration = fields.Char(string='Custom Declaration')
    quality_staff = fields.Char(string='Quality Staff')
    
    @api.model
    def _cron_generate_vessel_registration(self):
        # Thai lao them is_boned = transfer 29/11
        shipping_instruction = self.env['delivery.order'].search([
            ('date', '>=', '2022-10-01'),
            ('contract_id.type', '=', 'export'),
            ('is_bonded', '!=', 'transfer'),
            ('type', '=', 'Sale')
        ]).mapped('shipping_id')
        for ship in shipping_instruction:
            sql = """
            SELECT max(deli.date) as date from delivery_order deli
            join sale_contract as sc on sc.id = deli.contract_id
            WHERE deli.shipping_id = %s and deli.date >= '2022-10-01' and sc.type = 'export'
            """ % ship.id
            self.env.cr.execute(sql, ())
            for data in self.env.cr.fetchall():
                delivery_order = self.env['delivery.order'].search([
                    ('date', '=', data[0]),
                    ('shipping_id', '=', ship.id),
                    ('contract_id.type', '=', 'export')
                ])
                for deli in delivery_order:
                    if self.search([('shipping_instruction', '=', deli.shipping_id.id)]):
                        self.search([('shipping_instruction', '=', deli.shipping_id.id)]).write({
                            'do_date': deli.date
                        })
                    else:
                        value = {
                            'do_date': deli.date,
                            'shipping_instruction': deli.shipping_id.id,
                            'from_warehouse': deli.from_warehouse_id.id if deli.from_warehouse_id else False
                        }
                        self.env['vessel.registration'].create(value)


class DeliveryOrder(models.Model):
    _inherit = 'delivery.order'

    #err cẩn thận chưa biết
    # @api.model
    # def create(self, vals):
    #     result = super(DeliveryOrder, self).create(vals)
    #     if result:
    #         value = {
    #             'do_date': result.date,
    #             'shipping_instruction': result.shipping_id.id,
    #             'from_warehouse': result.from_warehouse_id.id if result.from_warehouse_id else False
    #         }
    #         self.env['vessel.registration'].create(value)
    #     return result

    
    
