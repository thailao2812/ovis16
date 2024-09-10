# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from datetime import date,datetime, timedelta


class ShippingInstruction(models.Model):
    _inherit = 'shipping.instruction'

    def _default_ico_lot(self):
        year = date.today().year
        lot = '14/1015/' + str(year)
        return lot

    no_of_teus = fields.Float(string='No. of container')
    dispatch_mode = fields.Selection([
        ('air', 'Air'),
        ('rail', 'Rail'),
        ('road', 'Road'),
        ('sea', 'Sea')
    ], string='Dispatch mode', default=None)
    loading_country = fields.Many2one('res.country', string='Loading Country')
    discharge_country = fields.Many2one('res.country', string='Discharge Country')
    destination_country = fields.Many2one('res.country', string='Destination Country')
    final_destination = fields.Many2one('delivery.place', string='Final Destination')
    country_origin = fields.Many2one('res.country', string='Country Origin')
    weights = fields.Selection([
        ('delivery_weight', 'Net Weight Delivery'),
        ('shipped_weight', 'Net Shipped Weight'),
        ('at_time', 'Net Weight at the time of receipt at the Curing Works'),
        ('re_weight', 'Re Weights'),
        ('net_shipping', 'Net Shipping Weight with 0.50% franchise')
    ], string='Weights', default=None)
    shipper = fields.Char(string='Shipper', default='SUCDEN COFFEE INDIA PRIVATE LIMITED')
    ship_to = fields.Many2one('res.partner', string='Ship To')
    ico_lot = fields.Char(string='ICO Lot No.', default=_default_ico_lot)
    ico_lot_description = fields.Char(string='ICO Lot No. Description')
    ship_to_address = fields.Char(string='Ship To Address')
    date_from = fields.Date(string='Delivery from')
    date_to = fields.Date(string='To')
    notify_1 = fields.Char(string='Notify 1')
    notify_2 = fields.Char(string='Notify 2')
    notify_3 = fields.Char(string='Notify 3')
    bag_mark = fields.Char(string='Bag Mark 1')
    against_sample = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string='Against Sample', default=None)
    freight = fields.Selection([
        ('collect', 'FREIGHT : COLLECT FROM CUSTOMER'),
        ('paid', 'PAID BY SUCDEN COFFEE NETHERLANDS BV')
    ], string='Freight', default=None)
    sample_approve_date = fields.Date(string='Sample Approve Date')
    shipment_from = fields.Many2one('stock.warehouse', string='Shipment From')
    forwarding_agent_id = fields.Many2one('res.partner', string='Forwarding Agent', domain=[('forwarding_agent_check', '=', True)])
    no_of_bag = fields.Float(string='No of bags', digits=(16, 0), related='shipping_ids.bags', store=True)
    packing_place = fields.Selection(selection='_get_new_packing_type', string='Stuffing place')
    status = fields.Selection(selection='_get_new_selection_type', string='Ship by')


    @api.model
    def _get_new_packing_type(self):
        return [('kushalnagar', 'Kushalnagar'),('mangalore', 'Mangalore')]

    @api.model
    def _get_new_selection_type(self):
        return [('kushalnagar', 'Factory - Kushalnagar'), ('mangalore', 'Factory - Mangalore')]

    @api.onchange('ship_to')
    def onchange_ship_to(self):
        for record in self:
            if record.ship_to:
                street = ', '.join([x for x in (record.ship_to.street, record.ship_to.street2) if x])
                if record.ship_to.district_id:
                    street += ' ' + record.ship_to.district_id.name + ' '
                if record.ship_to.city:
                    street += record.ship_to.city + ' '
                if record.ship_to.state_id:
                    street += record.ship_to.state_id.name
                record.ship_to_address = street

    def button_load_sc(self):
        res = super(ShippingInstruction, self).button_load_sc()
        for record in self:
            if record.contract_id:
                record.date_from = record.contract_id.date_from
                record.date_to = record.contract_id.date_to
            for line in record.shipping_ids:
                if line.packing_id:
                    line.gross_weight = line.product_qty + (line.bags * line.packing_id.tare_weight)
        return res


class ShippingInstructionLine(models.Model):
    _inherit = 'shipping.instruction.line'

    no_of_teus = fields.Float(string='No. of container')
    bags = fields.Float(string='Bags', digits=(16, 0))