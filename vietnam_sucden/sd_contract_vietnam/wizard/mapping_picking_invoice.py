# -*- encoding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError


class MappingGRN(models.TransientModel):
    _name = "mapping.picking.invoice"

    contract_id = fields.Many2one('purchase.contract', string="Contract")
    invoice_id = fields.Many2one('account.move', string="Invoice")
    stock_picking_ids = fields.One2many('stock.picking.allocated.wizard', 'wizard_mapping_id', string='GRN Allocate')

    @api.model
    def default_get(self, fields):
        res = super(MappingGRN, self).default_get(fields)
        active_id = self.env.context.get('active_id')
        move_id = self.env['account.move'].browse(active_id)
        purchase_contract = move_id.purchase_contract_id
        res['contract_id'] = purchase_contract.id if purchase_contract else False
        res['invoice_id'] = move_id.id if move_id else False
        return res

    def action_confirm(self):
        for rec in self:
            total_quantity = rec.invoice_id.total_quantity
            if sum(rec.stock_picking_ids.mapped('allocated_amount')) > total_quantity:
                raise UserError(_("The allocated quantity cannot higher than the total quantity of the invoice."))
            for pick in rec.stock_picking_ids:
                purchase_contract_id = rec.contract_id
                stock_allocation = self.env['stock.allocation'].search([
                    ('picking_id', '=', pick.picking_id.id), ('contract_id', '=', purchase_contract_id.id)
                ], limit=1)
                allocated_qty = stock_allocation.qty_allocation
                move_id = rec.invoice_id
                value = {
                    'invoice_id': move_id.id,
                    'picking_id': pick.picking_id.id,
                    'contract_id': rec.contract_id.id,
                    'allocated_qty': allocated_qty,
                    'allocated_amount': pick.allocated_amount,
                }
                self.env['stock.picking.allocated'].create(value)