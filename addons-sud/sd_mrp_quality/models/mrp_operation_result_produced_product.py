# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _, tools
import time
from datetime import timedelta
from odoo.exceptions import UserError, ValidationError


class MrpOperationResultProducedProduct(models.Model):
    _inherit = 'mrp.operation.result.produced.product'
    
    stack_wip_id = fields.Many2one('stock.lot',string='Stack Wip')
    
    def create_update_stack_wip(self):
        for line in self:
            if line.stack_wip_id:
                line.stack_wip_id._get_remaining_qty()
            else:
                zone_wip = self.env['stock.zone'].search([('location_wip','=',True),('warehouse_id','=',line.operation_result_id.warehouse_id.id)], limit = 1)
                if not zone_wip:
                    continue
                var = {
                    'production_id':line.operation_result_id.production_id.id,
                    'product_id':line.product_id.id,
                    'company_id':line.operation_result_id.warehouse_id.company_id.id,
                    'zone_id':zone_wip.id,
                    'packing_id':line.packing_id and line.packing_id.id or False,
                    #'hopper':this.hopper or False,
                    'date':time.strftime('%Y-%m-%d'),
                    'name':'/',
                    'warehouse_id':line.operation_result_id.warehouse_id.id,
                    'stack_type': 'stack_wip',
                    'stack_wip':True,
                }
                line.stack_wip_id = self.env['stock.lot'].create(var)
                line.stack_wip_id._get_remaining_qty()
    
        

