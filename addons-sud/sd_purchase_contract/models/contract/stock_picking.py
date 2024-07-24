# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

from datetime import datetime
import time
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%d-%m-%Y"

    
class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    purchase_contract_id = fields.Many2one('purchase.contract', string='Purchase Contract',
       readonly=True, states={'draft': [('readonly', False)]}, required=False,)
    
    
    @api.depends('move_line_ids_without_package.qty_done',
                 'move_line_ids_without_package',
                 'allocation_ids',
                 'allocation_ids.qty_allocation',
                 'allocation_ids.state')
    def _compute_allocation(self):
        for pick in self:
            qty = 0.0
            for allocation in pick.allocation_ids:
                if allocation.state !='draft':
                    qty += allocation.qty_allocation
            pick.allocated_qty = qty
            pick.qty_available = pick.total_qty - pick.allocated_qty
            if pick.qty_available <= 0.0:
                pick.allocated = True
        return  

    allocation_ids = fields.One2many('stock.allocation','picking_id', 'Allocation')
    allocated_qty = fields.Float(string='Allocated',compute='_compute_allocation',store=True, digits=(16, 0))
    qty_available = fields.Float(string='To Allocated',compute='_compute_allocation',store=True,digits=(16, 0))
    allocation_id = fields.Many2one('stock.allocation', string='Allocation',)
    allocated = fields.Boolean(string = 'Allocated',compute='_compute_allocation',default = False ,store=True)