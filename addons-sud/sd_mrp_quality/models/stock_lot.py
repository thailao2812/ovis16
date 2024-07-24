from operator import attrgetter
from re import findall as regex_findall, split as regex_split

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
import datetime
from odoo.tools import float_round


class StockLot(models.Model):
    _inherit = 'stock.lot'
       
    stack_wip = fields.Boolean(string='stack_wip', default= False)
    result_grp_line_ids = fields.One2many('mrp.operation.result.produced.product','stack_wip_id',string="Result GRP")
    
    @api.model
    @api.depends('result_grp_line_ids.picking_id','result_grp_line_ids.picking_id.state','result_grp_line_ids.picking_id.state_kcs',
                'result_grp_line_ids','result_grp_line_ids.product_qty','result_grp_line_ids.qty_bags','result_grp_line_ids.state',
                'move_line_ids', 'move_line_ids.picking_id.state', 'move_line_ids.qty_done','move_line_ids.bag_no', 'move_line_ids.location_id',
                'move_line_ids.location_dest_id', 'stack_empty','is_bonded', 'out_qty','move_line_ids.state', 'init_invetory_qty','init_invetory_bags','init_invetory')
    def _get_remaining_qty(self):
        for stack in self:
            if stack.result_grp_line_ids:
                if stack.result_grp_line_ids.filtered(lambda x: x.picking_id.state == 'done'):
                    stack.init_qty = 0
                    stack.remaining_qty = 0
                    stack.stack_qty = 0
                    stack.bag_qty = 0
                elif stack.result_grp_line_ids.filtered(lambda x: x.picking_id.state_kcs == 'rejected'): 
                    stack.init_qty = 0
                    stack.remaining_qty = 0
                    stack.stack_qty = 0
                    stack.bag_qty = 0
                
                elif stack.result_grp_line_ids.filtered(lambda x: x.state == 'cancel'): 
                    stack.init_qty = 0
                    stack.remaining_qty = 0
                    stack.stack_qty = 0
                    stack.bag_qty = 0
                    
                else:
                    for i in stack.result_grp_line_ids:
                        stack.init_qty = i.product_qty
                        stack.remaining_qty = i.product_qty
                        stack.stack_qty = i.product_qty
                        stack.bag_qty = i.qty_bags
            else:
                return super(StockLot, self)._get_remaining_qty()
    
    @api.depends('result_grp_line_ids.picking_id','result_grp_line_ids.picking_id.state',
                 'result_grp_line_ids','result_grp_line_ids.product_qty',
                 'move_line_ids', 
                 'move_line_ids.picking_id.state_kcs',
                 'move_line_ids.picking_id.state', 
                 'move_line_ids.picking_id.kcs_line', 
                 'move_line_ids.init_qty')
    def _compute_qc(self):
         for stack in self:
            if stack.result_grp_line_ids:
                for i in stack.result_grp_line_ids:
                    stack.packing_id = i.packing_id and i.packing_id.id or False
                    stack.production_id = i.production_id and i.production_id.id or False
            else:
                super(StockLot, self)._compute_qc()
                    
    
    
    
