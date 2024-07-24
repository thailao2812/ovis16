# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from datetime import datetime
    
    
class XExternalWarehouse(models.Model):
    _name = 'x_external.warehouse'

    x_name = fields.Char('Name', size=256)
    name = fields.Char('Name', size=256)
    
    def _default_warehouse(self):
        warehouse_ids = self.env['stock.warehouse'].with_context(user_workers=True).search(
            [('company_id', '=', self.env.user.company_id.id)])
        # default with user only working 1 company account analytic
        if warehouse_ids:
            return warehouse_ids[0]
    
    @api.model
    def _domain_warehouse(self):
        return "[('id', 'in', %s)]" % self.env.user._warehouses_domain()
    
    
    x_warehouse_id = fields.Many2one('stock.warehouse', string= 'Internal Warehouse', default=_default_warehouse, domain=lambda self: self._domain_warehouse())
    
    # def name_get(self):
    #     return [(ex.id, '%s' % (ex.x_name)) for ex in self]
    
