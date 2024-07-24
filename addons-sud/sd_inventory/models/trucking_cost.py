# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from odoo.tools import float_round

class StockTrucckingCost(models.Model):
    _name = 'stock.trucking.cost'
    
    name = fields.Char(string="Name")
    cost = fields.Float(string="Cost/Kg")
    
        
        
class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    @api.depends('truking_cost_id')
    def compute_cost(self):
        for i in self:
            if i.truking_cost_id and i.total_qty!=0:
                i.cost = i.truking_cost_id.cost 
            
        
    truking_cost_id = fields.Many2one('stock.trucking.cost', 'Truking cost')
    cost = fields.Float(string="VND/Kg",compute ='compute_cost', store = True )
    