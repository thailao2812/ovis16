# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID


class CreateStockStack(models.TransientModel):
    _inherit = 'create.stock.stack'

    building_id = fields.Many2one('building.warehouse', string='Building')

    def create_stack(self):
        move_line_id = self._context.get('active_id')
        move = pick_info = self.env['stock.move.line'].browse(move_line_id)
        pick_info = move.picking_id
        stack_id = False
        if pick_info.pcontract_id:
            stack_id = pick_info.pcontract_id.wr_line and pick_info.pcontract_id.wr_line or False
        for this in self:
            # Get name
            # if self.hopper:
            #     name = self.env['ir.sequence'].next_by_code('stock.stack.hopper.seq') or 'New'
            # else:
            #     name = self.env['ir.sequence'].next_by_code('stock.sack.seq') or 'New'
            var = {
                'product_id': move.product_id.id,
                'company_id': pick_info.company_id.id,
                'zone_id': this.zone_id.id,
                # 'hopper':this.hopper or False,
                'date': this.date,
                'name': '/',
                'stack_type': this.stack_type,
                'districts_id': this.districts_id.id or False,
                'p_contract_id': pick_info.pcontract_id and pick_info.pcontract_id.id or 0,
                'warehouse_id': pick_info.warehouse_id and pick_info.warehouse_id.id or False,
                'building_id': this.building_id and this.building_id.id or False
            }
            if pick_info.warehouse_id.x_is_bonded:
                var.update({'is_bonded': True})
            if not stack_id:
                stack_id = self.env['stock.lot'].create(var)

            move.lot_id = stack_id and stack_id.id or False
            move.zone_id = this.zone_id.id
            if pick_info.pcontract_id:
                pick_info.pcontract_id.wr_line = stack_id
        return True