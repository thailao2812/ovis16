# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from datetime import datetime

class MrpOperationResult(models.Model):
    _inherit = "mrp.operation.result"

    @api.depends('produced_products','produced_products.product_qty')
    def _compute_line_qty(self):
        for line in self:
            total_qty = 0.0
            for produced_line in line.produced_products:
                total_qty += produced_line.product_qty
            line.total_line_qty = total_qty

    @api.depends('produced_products','produced_products.product_id')
    def _compute_line_product(self):
        for line in self:
            all_products = all_pending_grn = all_stack_wip = ''
            for produced_line in line.produced_products:
                if all_products == '':
                    all_products = produced_line.product_id.default_code
                    all_pending_grn = produced_line.pending_grn
                    # all_stack_wip = produced_line.stack_wip_id.name
                else:
                    all_products = "{}; {}".format(all_products, produced_line.product_id.default_code)
                    all_pending_grn = "{}; {}".format(all_pending_grn, produced_line.pending_grn)
                    # all_stack_wip = "{}; {}".format(all_stack_wip, produced_line.stack_wip_id.name)
            line.all_line_products = all_products
            line.all_pending_grn = all_pending_grn
            # line.all_stack_wip = all_stack_wip

    scale_ids = fields.One2many('mrp.operation.result.scale','operation_result_id',string="Weight Scale")
    total_line_qty = fields.Float(compute='_compute_line_qty', string='Qty', default=0, store= True)
    all_line_products = fields.Char(compute='_compute_line_product', string='Products', store= True)
    all_pending_grn = fields.Char(compute='_compute_line_product', string='Pending GRN', store= True)
    # all_stack_wip = fields.Char(compute='_compute_line_product', string='Stack WIP', store= True)

        
class MrpOperationResultProducedProduct(models.Model):
    _inherit = 'mrp.operation.result.produced.product'

    tare_weight = fields.Float('Tare Weight')
    scale_grp_id = fields.Integer('Scale GRP ID', readonly=True)
    mor_line_ids = fields.One2many('mrp.operation.result.scale','mor_line_id',string="Mor Scale Line")
    # app_mor_id = fields.Integer('App MOR_ID', readonly=True)
    
class MrpOperationResultScale(models.Model):
    _name = 'mrp.operation.result.scale'
    
    operation_result_id = fields.Many2one('mrp.operation.result',string="Weight Scale")
    mor_line_id = fields.Many2one('mrp.operation.result.produced.product',string="Scale Lines")
    product_id = fields.Many2one('product.product', string='Product')
    packing_id = fields.Many2one('ned.packing', string='Packing')
    packing_branch_id = fields.Many2one('sud.packing.branch', string='Pallet')
    weight_scale = fields.Float('Gross Weight')
    bag_no = fields.Float('Bags No.')
    tare_weight = fields.Float('Tare Weight')
    net_weight = fields.Float('NET Weight', readonly=True)
    bag_code = fields.Char('Bag Code', readonly=True)
    old_weight = fields.Float('Old Weight')
    usr_api_create= fields.Many2one('res.users', 'API Created by', readonly=True)
    create_date= fields.Datetime('Created Date', readonly=True)
    scale_grp_id = fields.Integer('Scale GRP ID', readonly=True)
    scale_grp_line_id = fields.Integer('Scale GRP Line ID', readonly=True)
    shift_name = fields.Char('Shift Name', readonly=True)
    # pallet_type_id = fields.Many2one('ned.packing', string='Pallet')
    pallet_weight = fields.Float('Pallet Weight')
    lining_bag = fields.Boolean(string='Lining Bags',default=False)
    picking_scale_id = fields.Many2one('stock.picking',string="Weight Scale")
    gip_line_id = fields.Many2one('stock.move.line',string="Scale Lines")
    scale_gip_id = fields.Integer('Scale GIP ID', readonly=True)
    scale_gip_line_id = fields.Integer('Scale GIP Line ID', readonly=True)
    state_scale = fields.Selection(selection=[('approved', 'Approved'),('cancel', 'Cancel')],string='Scale State', readonly=True, copy=False, index=True, default='approved', tracking=True,)
    scale_no = fields.Char('Scale No.', readonly=True)


class StockPicking(models.Model):
    _inherit = "stock.picking"
    _order = 'id desc'

    scale_ids = fields.One2many('mrp.operation.result.scale','picking_scale_id',string="Weight Scale")


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    scale_gip_id = fields.Integer('Scale GIP ID', readonly=True)
    gip_line_ids = fields.One2many('mrp.operation.result.scale','gip_line_id',string="GIP Scale Line")

