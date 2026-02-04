# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import UserError
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class ReturnGoodsCSContract(models.Model):
    _name = "return.goods.cs.contract"
    _description = "Return Goods CS Contract"

    contract_id = fields.Many2one('purchase.contract')
    reason = fields.Char(string="Reason")
    quantity = fields.Integer(string="Quantity")
    date_request = fields.Datetime(string="Date Request")
    state = fields.Selection([
        ('requested', 'Requested'),
        ('commercial', 'Approve by Commercial Manager'),
        ('rejected', 'Rejected'),
    ])
    reason_reject = fields.Char(string="Reason Rejected")
    picking_id = fields.Many2one('stock.picking', string='Return Picking')

    def approve_commercial(self):
        self.state = 'commercial'
        self.contract_id.state_return = 'done'
        contract = self.contract_id
        quantity = self.quantity
        if not contract.delivery_place_id.warehouse_id:
            raise UserError(_("Warehouse cannot be empty"))
        picking_type = self.env['stock.picking.type'].search([
            ('warehouse_id', '=', contract.delivery_place_id.warehouse_id.id),
            ('code', '=', 'return_supplier')
        ], limit=1)
        if not picking_type:
            raise UserError(_("Picking type cannot be empty"))
        value = {
            'partner_id': contract.partner_id.id,
            'warehouse_id': contract.delivery_place_id.warehouse_id.id,
            'picking_type_id': picking_type.id
        }
        picking = self.env['stock.picking'].create(value)
        for line in self.contract_id.contract_line:
            value_line = {
                'picking_id': picking.id,
                'product_id': line.product_id.id,
                'init_qty': self.quantity,
            }
            self.env['stock.move.line'].create(value_line)
        contract.picking_return_ids = [(4, picking.id)]
        self.picking_id = picking.id

    def action_reject(self):
        if not self.reason_reject:
            raise UserError(_("Reason reject need to be filled"))
        self.state = 'rejected'
        self.contract_id.state_return = 'rejected'