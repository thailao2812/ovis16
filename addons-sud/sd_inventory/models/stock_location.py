# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

class Location(models.Model):
    _inherit = "stock.location"

    usage = fields.Selection(selection_add=[('procurement','Procurement')], 
            default='internal',
            ondelete={'supplier': 'set default',
                    'view': 'set default',
                    'internal': 'set default',
                    'customer': 'set default',
                    'inventory': 'set default',
                    'production': 'set default',
                    'procurement': 'set default',
                    'transit': 'set default'})
    
    
    
    def name_get(self):
        result = []
        for pro in self:
            result.append((pro.id, pro.name))
        return result
    
