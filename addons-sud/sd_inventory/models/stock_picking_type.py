# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

selection_code =[
      ('transfer_out', 'Transfer Out'),
      ('transfer_in', 'Transfer In'),
      ('return_customer', 'Return Customers'), 
      ('return_supplier', 'Return Supplier'), 
      ('production_out', 'Production Out'),
      ('production_in', 'Production In'),
      ('phys_adj', 'Physical Adjustment'),
      ('material_in','Material In'),
      ('material_out','Material Out'),
      ('adjust_stock','Adjust stock')]
    
class StockPickingType(models.Model):
    _inherit = "stock.picking.type"
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('warehouse_id',True):
                vals['warehouse_id']= False
        return super().create(vals_list)
    
    code = fields.Selection(selection_add= selection_code, string= 'Type of Operation', required=True, default="incoming", 
            ondelete={'transfer_out': 'set default',
                'transfer_in': 'set default',
                'return_customer': 'set default',
                'return_supplier': 'set default',
                'production_out': 'set default',
                'production_in': 'set default',
                'phys_adj': 'set default',
                'material_in': 'set default',
                'material_out': 'set default',
                'adjust_stock': 'set default',}
            )
        
    is_service = fields.Boolean('Service')
    is_product = fields.Boolean('Product')
    is_materials = fields.Boolean('Materials')
    is_tools = fields.Boolean('Tools')
    is_consignment_agreement = fields.Boolean('Consignment Agreement')
    dashboard_invisible = fields.Boolean('Dashboard Invisible')
    
        #THANH: For Security purpose (Filter data for user belong)
    res_user_ids = fields.Many2many('res.users', 'picking_type_users_ref','user_id','picking_type_id', string= 'Allowed Users')
        #Kiet: Transfer 
    transfer_picking_type_id = fields.Many2one('stock.picking.type', 'Picking type for transfer')
    operation = fields.Selection([
            ('none','None'),
            ('station','Station'),
            ('factory','Factory'),], string='Operation')
    
    fob = fields.Boolean('FOB')
    kcs = fields.Boolean(string="KCS")
    deduct = fields.Boolean(string="Deduct")
    kcs_approved = fields.Boolean(string="Kcs Approved Picking")
    
    picking_type_npe_id = fields.Many2one('stock.picking.type', string='Picking type for NPE')
    picking_type_nvp_id = fields.Many2one('stock.picking.type', string='Picking type for NVP')
    stack = fields.Boolean(string="Stack")

