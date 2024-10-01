# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
import math


class DeliveryReady(models.Model):
    _name = 'delivery.ready'

    delivery_id = fields.Many2one('ned.security.gate.queue', string='DR')
    license_plate = fields.Char(string='Vehicle No.', related='delivery_id.license_plate', store=True)
    arrivial_time = fields.Datetime('Arrival Time', related='delivery_id.arrivial_time', store=True)
    supplier_id = fields.Many2one('res.partner', related='delivery_id.supplier_id', store=True)
    approx_quantity = fields.Float('Estimated Quantity', related='delivery_id.approx_quantity', store=True)
    request_payment_id = fields.Many2one('request.payment', ondelete='cascade')
    percent = fields.Integer(string='%', default=70)
    total_qty = fields.Float(string='Total Qty', compute='compute_total_qty', store=True, digits=(12, 0))
    quantity = fields.Float(string='Quantity DR', related='delivery_id.approx_quantity', store=True, digits=(12, 0))
    remain_qty = fields.Float(string='Remain Qty', compute='compute_remain_qty', store=True, digits=(12, 0))
    paid_quantity = fields.Float(string='Paid Qty', compute='compute_paid_qty', store=True, digits=(12, 0))
    request_qty = fields.Float(string='Request Qty', digits=(12, 0))

    def custom_round(self, number: float) -> int:
        if number - round(number) == 0.5:
            return math.ceil(number)
        else:
            return round(number)

    @api.depends('delivery_id', 'percent', 'quantity')
    def compute_total_qty(self):
        for rec in self:
            rec.total_qty = self.custom_round(rec.quantity * rec.percent / 100)

    @api.depends('delivery_id')
    def compute_paid_qty(self):
        for rec in self:
            paid_quantity = 0
            if self.env.context.get('seq'):
                delivery_ready_in_current_contract = self.env['delivery.ready'].search([
                    ('delivery_id', '=', rec.delivery_id.id),
                    ('request_payment_id.purchase_contract_id', '=', self.env.context.get('purchase_contract_id')),
                    ('request_payment_id.name', '<', int(self.env.context.get('seq')))
                ])
                delivery_ready_other_contract = self.env['delivery.ready'].search([
                    ('delivery_id', '=', rec.delivery_id.id),
                    ('request_payment_id.purchase_contract_id', '!=', self.env.context.get('purchase_contract_id'))
                ])
                if delivery_ready_in_current_contract:
                    paid_quantity = sum(delivery_ready_in_current_contract.mapped('request_qty'))
                if delivery_ready_other_contract:
                    paid_quantity = sum(delivery_ready_other_contract.mapped('request_qty'))
                rec.paid_quantity = paid_quantity
            else:
                request_payment = rec.request_payment_id
                delivery_ready_in_current_contract = self.env['delivery.ready'].search([
                    ('delivery_id', '=', rec.delivery_id.id),
                    ('request_payment_id.purchase_contract_id', '=', request_payment.purchase_contract_id.id),
                    ('request_payment_id', '!=', request_payment.id),
                    ('request_payment_id.name', '<', int(request_payment.name))
                ])
                delivery_ready_other_contract = self.env['delivery.ready'].search([
                    ('delivery_id', '=', rec.delivery_id.id),
                    ('request_payment_id.purchase_contract_id', '!=', request_payment.purchase_contract_id.id)
                ])
                if delivery_ready_in_current_contract:
                    paid_quantity += sum(delivery_ready_in_current_contract.mapped('request_qty'))
                if delivery_ready_other_contract:
                    paid_quantity += sum(delivery_ready_other_contract.mapped('request_qty'))
                rec.paid_quantity = paid_quantity

    @api.depends('request_qty', 'paid_quantity', 'total_qty')
    def compute_remain_qty(self):
        for rec in self:
            rec.remain_qty = rec.total_qty - rec.paid_quantity - rec.request_qty
            if rec.remain_qty < 0:
                raise UserError(_("Remain Quantity cannot < 0!!!"))
