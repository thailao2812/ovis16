# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"
    
    wh_raw_material_loc_id = fields.Many2one('stock.location', string = 'Raw Material Stock')
    wh_finished_good_loc_id = fields.Many2one('stock.location', string = 'Finished Goods Stock')
    wh_production_loc_id =  fields.Many2one('stock.location', string = 'Production Stock')
    production_in_type_id = fields.Many2one('stock.picking.type', string = 'Production Type - In')
    production_out_type_id = fields.Many2one('stock.picking.type', string = 'Production Type - Out')
    return_customer_type_id = fields.Many2one('stock.picking.type', string = 'Customer Returns')
    return_supplier_type_id = fields.Many2one('stock.picking.type', string = 'Supplier Returns')
    other_location_loc_id = fields.Many2one('stock.location', string ='Other Location')
    adj_type_id = fields.Many2one('stock.picking.type', string='ADJ Stock')
    
    wh_npe_id = fields.Many2one('stock.location', 'NPE')
    wh_nvp_id =fields.Many2one('stock.location', 'NVP')
    
    production_out_type_consu_id = fields.Many2one('stock.picking.type', 'Production Type Material - Out')
    transfer_in_id = fields.Many2one('stock.picking.type', 'Transfer In')
    transfer_out_id = fields.Many2one('stock.picking.type', 'Transfer Out')
    out_type_local_id = fields.Many2one('stock.picking.type', 'Delivery Local')
    x_is_bonded = fields.Boolean(string='Is Bonded Warehouse')
    code = fields.Char(string='Code', size=12)
    
    account_analytic_id =  fields.Many2one('account.analytic.account','Account Analytic')
    
    x_auto_done = fields.Boolean(string='Is Warehouse Factory')
    
    
    def name_get(self):
        result = []
        for pro in self:
            result.append((pro.id, pro.code))
        return result
