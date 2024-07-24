# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from datetime import datetime
    
    
class XExternalWarehouse(models.Model):
    _inherit = 'x_external.warehouse'

    x_name = fields.Char('Name', size=256)
    x_warehouse_id = fields.Many2one('stock.warehouse', 'Internal Warehouse')
    
