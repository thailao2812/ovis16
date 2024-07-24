# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_qc_assigned(self):
        res = super().button_qc_assigned()
        for record in self:
            transfer_order = False
            if record.picking_type_id.code == 'transfer_out' or record.picking_type_id.code == 'transfer_in':
                transfer_order = record.delivery_id
            if record.picking_type_id.code == 'transfer_in':
                transfer_order.gtr_picking_id = record.id
            if record.picking_type_id.code == 'transfer_out':
                transfer_order.picking_id = record.id
        return res