# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class StockAllocation(models.Model):
    _inherit = "stock.allocation"

    qty_allocation_net = fields.Float(string='Qty Allocation (Gross Qty)', digits=(12, 0))
    qty_received_net = fields.Float(compute='_compute_qty_net', string='Allocated (Gross Qty)', store=True, digits=(12, 0))
    qty_unreceived_net = fields.Float(compute='_compute_qty_net', string='UnAllocated (Gross Qty)', digits=(12, 0), store=True)

    @api.depends('contract_id', 'picking_id', 'qty_allocation_net', 'state')
    def _compute_qty_net(self):
        for order in self:
            allocation_qty = 0.0
            if order.picking_id and order.contract_id:

                allocation_obj = self.env['stock.allocation'].search([('picking_id', '=', order.picking_id.id)])
                allocation_qty = sum(allocation_obj.mapped('qty_allocation_net'))
                order.qty_received_net = allocation_qty or 0.0

                move_line = order.picking_id.move_line_ids_without_package.filtered(
                    lambda r: r.picking_id.state == 'done')
                qty_grn = sum(move_line.mapped('init_qty'))
                order.qty_unreceived_net = qty_grn - allocation_qty


            else:
                order.qty_received_net = 0
                order.qty_unreceived_net = 0

            if order.qty_unreceived_net < 0:
                raise UserError(_('unReceived Net must larger than 0'))

    def approve_allocation(self):
        for allocation in self:
            if allocation.contract_id.type == 'purchase' and allocation.contract_id.origin:
                raise UserError(_("You don't need to allocate into this contract, because it converted from CS already!!!"))
            if allocation.qty_allocation_net == 0:
                raise UserError(_("Please input Qty Allocation (Net Qty) before approve this Allocation!!!"))
            allocation.state = 'approved'
            allocation.contract_id.qty_received = allocation.contract_id.qty_received + allocation.qty_allocation
            allocation._compute_qty_net()
            allocation._compute_qty()
        return True
