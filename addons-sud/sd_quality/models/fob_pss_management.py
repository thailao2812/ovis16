# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from datetime import datetime
  
    
class FOBPSSManagement(models.Model):
    _name ="fob.pss.management"
    _order = "id desc"
    
    def btt_confirm(self):
        print(12)
        return self.write({'state': 'approve'})

    def btt_draft(self):
        return self.write({'state': 'draft'})
    
    def btt_view(self):
        return {}
    

    name = fields.Char(string="PSS name")
#    shipping_id = fields.Many2one("shipping.instruction", string="SI No.")
    created_date =  fields.Date(string="Date")
    date_sent = fields.Date(string="Date sent")
    pss_status = fields.Selection([('pending', 'Pending'), ('sent', 'Sent'), ('approved', 'Approved'), ('rejected','Rejected')], string="PSS status")
    date_result = fields.Char(string="Date result")
    product_id = fields.Many2one('product.product', string='Product')
    buyer_ref = fields.Char(string="Buyer ref.")
    lot_quantity = fields.Float(string="Quantity")
    cont_quantity = fields.Float(string="Cont. qty.")
    mc = fields.Float(string="MC")
    fm = fields.Float(string="FM")
    black = fields.Float(string="Black")
    broken = fields.Float(string="Broken")
    brown = fields.Float(string="Brown")
    moldy = fields.Float(string="Moldy")
    burned = fields.Float(string="Burned")
    scr20 = fields.Float(string="Screen 20")
    scr19 = fields.Float(string="Screen 19")
    scr18 = fields.Float(string="Screen 18")
    scr16 = fields.Float(string="Screen 16")
    scr13 = fields.Float(string="Screen 13")
    scr12 = fields.Float(string="Screen 12")
    blscr12 = fields.Float(string="Below scr.12")
    stack = fields.Many2many('stock.lot', 'stock_stack_pss_rel', 'pss_id', 'stack_id', string='Stack no.')
    ref_no = fields.Char(string="Reference")
    inspector = fields.Char(string="Inspector")
    buyer_comment = fields.Char(string="Buyer's comment")
    our_comment = fields.Char(string="Our comment")
    note = fields.Char(string="Note")
    qc_staff = fields.Char(string="QC staff")
    partner_id = fields.Many2one("res.partner", string="Customer")
    bulk_density = fields.Char(string='Bulk Density')
    shipment_date = fields.Date(string='Shipment Date')
    state = fields.Selection([('draft','Draft'), ('approve', 'Approved')], string='Status', default='draft')
    
    shipper_id = fields.Many2one("res.users" ,string="Shipper")
    file = fields.Binary(string='File')
    file_name = fields.Char(string='File Name')
    buyer_ref_name = fields.Char(string='Buyer Ref')
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
    
    date_sampling= fields.Date(string="Date sampling")
    inspected_by = fields.Char(string="Inspected by/ Sampler")
    qc_staff = fields.Char(string="QC staff")
    awb_no = fields.Char(string="AWB No")
    x_shipper = fields.Many2one('res.partner', 'Shipper')
    x_ex_warehouse = fields.Many2one('x_external.warehouse', 'Warehouse')
    x_traffic_contract = fields.Many2one('traffic.contract', 'S Contract')
    x_screen14 = fields.Float('Screen 14')
    x_screen15 = fields.Float('Screen 15')
    x_screen17 = fields.Float('Screen 17')
    
    
