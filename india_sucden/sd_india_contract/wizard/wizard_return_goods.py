# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"


class WizardReturnGoods(models.TransientModel):
    _name = "wizard.return.goods"

    contract_id = fields.Many2one('purchase.contract')
    unfixed_qty = fields.Float(string="Unfixed Qty", related='contract_id.qty_unfixed', store=True)
    quantity = fields.Float(string="Quantity")
    reason = fields.Char(string="Reason")

    @api.onchange('quantity')
    def onchange_quantity(self):
        if self.quantity > self.unfixed_qty:
            raise UserError(_("Quantity cannot be greater than unfixed"))

    @api.model
    def default_get(self, fields):
        res = {}
        active_id = self._context.get('active_id')
        if active_id:
            contract = self.env['purchase.contract'].browse(active_id)
            res = {'contract_id': contract.id}
        return res

    def button_request(self):
        if self.contract_id:
            value = {
                'reason': self.reason,
                'contract_id': self.contract_id.id,
                'quantity': self.quantity,
                'state': 'requested'
            }
            self.env['return.goods.cs.contract'].create(value)
            self.contract_id.state_return = 'requested'

    def button_confirm(self):
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
