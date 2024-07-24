# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

class KcsGlyphosate(models.Model):
    _name ="kcs.glyphosate"
    _order = "id desc"
    
    created_date =  fields.Date(string="Date")
    name = fields.Char(string="PSS name", size=256)
    
    si_id = fields.Many2one('shipping.instruction',string="SI No")
    customer_id = fields.Many2one('res.partner',string= "Customer")
    product_id = fields.Many2one('product.product', string='Product')
    test_requirement = fields.Char(string="Test Requirement")
    date_sent = fields.Date(string="Date sent")
    pss_status = fields.Selection([('pending', 'Pending'), ('sent', 'Sent'), ('approved', 'Approved'), ('rejected','Rejected')], string="PSS status")
    date_result = fields.Date(string="Date result")
    quantity = fields.Float(string="Quantity")
    cont_qty = fields.Float(string="Cont. qty.")
    stack_no = fields.Many2one('stock.lot',string="Stack No.")
    original = fields.Char(string="Original")
    our_comment = fields.Char(string="Our comment")
    analysis_by = fields.Char(string="Analysis by")
    results  = fields.Float(string="Results")
    inspector_by = fields.Char(string="Inspector by")
    qc_staff = fields.Char(string="QC staff")
    remark = fields.Char(string="Remark")
    
    def _default_warehouse(self):
        warehouse_ids = self.env['stock.warehouse'].with_context(user_workers=True).search(
            [('company_id', '=', self.env.user.company_id.id)])
        # default with user only working 1 company account analytic
        if warehouse_ids:
            return warehouse_ids[0]
    
    @api.model
    def _domain_warehouse(self):
        return "[('id', 'in', %s)]" % self.env.user._warehouses_domain()
    
    warehouse_id = fields.Many2one('stock.warehouse',string= "Warehouse", default=_default_warehouse, domain=lambda self: self._domain_warehouse())



        