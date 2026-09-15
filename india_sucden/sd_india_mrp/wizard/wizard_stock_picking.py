# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID


class wizard_stock_picking(models.TransientModel):
    _inherit = "wizard.stock.picking"

    def prepare_stock_picking(self):
        value = super(wizard_stock_picking, self).prepare_stock_picking()
        active_id = self._context.get('active_ids')
        result_obj = self.env['request.materials.line'].browse(active_id)
        if result_obj.picking_grn_id:
            value['picking_grn_id'] = result_obj.picking_grn_id.id
        return value
