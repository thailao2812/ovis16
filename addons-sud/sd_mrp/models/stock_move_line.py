# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from datetime import datetime
    
    
class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'
    
    finished_id = fields.Many2one('mrp.production', string="Fin Production")
    material_id = fields.Many2one('mrp.production', string="Material Production")




    
    
    
    
    
    

