# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"

class RequestPaymentLine(models.Model):
    _name = "request.payment.line"
    _description = 'Detail of Payment Request'

    name = fields.Char('Vehicle No', size=128)
    delivery_id = fields.Many2one('ned.security.gate.queue', 'Delivery Registration')
    grn_id = fields.Many2one('stock.picking', 'GRN')
    percent = fields.Selection([('70', 70), ('90', 90), ('100', 100)], string='Percent', default='70')
    amount = fields.Float('Amount')
    request_id = fields.Many2one('request.payment', 'Payment Request')
    request_id_npe = fields.Many2one('request.payment', 'Payment Request')
    estimated_quantity = fields.Float(string="Estimated Quantity")
    quantity_payment = fields.Float(string="Advance Quantity")
    quantity_remain_payment = fields.Float(string="Remain Quantity")
    price_unit = fields.Float(string="Market Price")
    limit_quantity_payment = fields.Float(string='Limit Quantity Payment')
    #
    # @api.onchange('quantity_payment')
    # def onchange_quantity_payment(self):
    #     if self.quantity_payment > self.limit_quantity_payment:
    #         raise UserError(_("You cannot set Quantity Payment more than %s") % self.limit_quantity_payment)

    # @api.model
    # def create(self, vals):
    #     print '>>> parent  >>>>>  ', self.env.context
    #     request_id = self.env.context.get('request_id', False)
    #     return super(RequestPaymentLine, self).with_context({'request_id': request_id}).create(vals)
    @api.onchange('price_unit', 'quantity_payment', 'percent')
    def onchange_price_unit(self):
        if self.price_unit and self.percent and self.quantity_payment:
            self.amount = (self.price_unit * self.quantity_payment) * (float(self.percent)/100)

    @api.depends('delivery_id', 'percent')
    @api.onchange('delivery_id', 'percent')
    def get_qty_payment(self):
        qty_payment = 0
        for res in self:
            qty_payment = 0
            if res.delivery_id:
                qty_payment += res.delivery_id.approx_quantity
            unit_price = 0
            if res.request_id:
                if res.request_id.purchase_contract_id:
                    unit_price = res.request_id.purchase_contract_id.contract_line[0].price_unit
            res.amount = qty_payment * unit_price * float(res.percent) / 100
            res.quantity_payment = res.delivery_id.approx_quantity * float(res.percent) / 100
            res.name = res.delivery_id.license_plate
            res.estimated_quantity = qty_payment
            if res.request_id.purchase_contract_id:
                res.price_unit = res.request_id.purchase_contract_id.contract_line[0].price_unit
            res.grn_id = res.delivery_id and res.delivery_id.link_fot_id and res.delivery_id.link_fot_id.id or False
            
            contract_ids = self.env['request.payment.line'].search([])
            contract_ids = contract_ids.mapped('delivery_id')
            
            domain = {'grn_id':[('id','=',res.delivery_id.link_fot_id.id)],'delivery_id': [('supplier_id', '=', res.request_id.partner_id.id),('id', 'not in', contract_ids.ids),
                                                                                           ('product_ids','in',res.request_id.purchase_contract_id.product_id.id)]}
        return {'domain':domain}


class RequestPaymentLineConvert(models.Model):
    _name = 'request.payment.line.convert'

    request_id = fields.Many2one('request.payment')
    fixation_qty = fields.Float(string='Fixation Qty')
    contract_id = fields.Many2one('purchase.contract', string='Contract No.')
    provisional = fields.Float(string='Provisional')
    advance_payment = fields.Float(string='Advance Payment')
    advance_date = fields.Date(string='Advance Date')
    rate_date = fields.Float(string="Interest rate/Date")
    total_days = fields.Float(string='Total Days')
    interest = fields.Float(string='Interest')
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date to')

#######################################################################################
    