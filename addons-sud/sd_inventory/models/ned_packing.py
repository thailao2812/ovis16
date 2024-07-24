# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
import re
# from pip._vendor.pygments.lexer import _inherit
DATE_FORMAT = "%Y-%m-%d"
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class NedPacking(models.Model):
    _inherit = 'ned.packing'
    
        
    def _default_warehouse(self):
        warehouse_ids = self.env['stock.warehouse'].with_context(user_workers=True).search(
            [('company_id', '=', self.env.user.company_id.id)])
        # default with user only working 1 company account analytic
        if warehouse_ids:
            return warehouse_ids[0]
    
    @api.model
    def _domain_warehouse(self):
        return "[('id', 'in', %s)]" % self.env.user._warehouses_domain()
        
    warehouse_id = fields.Many2one('stock.warehouse',string="Warehouse", default=_default_warehouse, domain=lambda self: self._domain_warehouse())
    
    repair_line_ids = fields.One2many('ned.packing.line','packing_id', string="Repair History")

    
class NedPackingRepairLine(models.Model):
    _name = 'ned.packing.line'


    # @api.onchange('product_id')
    # def _onchange_product_id(self):
    #     for this in self:
    #         if this.product_id:
    #             this.name = this.product_id.product_tmpl_id.name or False
    #             this.product_uom = this.product_id.product_tmpl_id.uom_id or False

    packing_id = fields.Many2one('ned.packing', string="Code")
    descriptions = fields.Char(string='Descriptions')
    product_uom = fields.Many2one('uom.uom', string="Uom")
    tare_weight = fields.Float(string='Tare Weight', default=0.0, digits=(12, 0))
    remarks = fields.Char(string='Remarks')



