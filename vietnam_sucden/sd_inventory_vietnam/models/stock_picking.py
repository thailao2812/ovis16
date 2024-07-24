# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
import time
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import timedelta, datetime, date


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    stack_type = fields.Selection(related='lot_id.stack_type', store=True)
    shipping_instruction_id = fields.Many2one('shipping.instruction', string='SI No.')
    
    state_kcs = fields.Selection(
        selection=[('draft', 'New'), ('approved', 'Approved'), ('waiting', 'Waiting Another Operation'),
                   ('rejected', 'Rejected'), ('cancel', 'Cancel')], string='KCS Status', readonly=True, copy=False,
        index=True, default='draft', tracking=True, )

    def button_sd_validate(self):
        for record in self:
            if record.picking_type_id.code == 'incoming' and record.picking_type_id.operation == 'factory':
                net_qty = record.total_init_qty
                basis_qty = 0
                if record.state_kcs == 'approved':
                    for line in record.kcs_line:
                        line.product_qty = net_qty
                        line._compute_deduction()
                        basis_qty = line.basis_weight
                    for ml in record.move_line_ids_without_package:
                        ml.qty_done = basis_qty
        return super(StockPicking, self).button_sd_validate()