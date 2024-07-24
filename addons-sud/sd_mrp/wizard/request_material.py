# -*- coding: utf-8 -*-

import time
from datetime import datetime
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from odoo.tools import float_round
import time
from datetime import timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import timedelta, datetime, date
import calendar

class wizard_stock_move(models.TransientModel):
    _name = "wizard.stock.move"
    
    wizard_id = fields.Many2one('wizard.stock.picking', 'Wizard Stock Picking', ondelete='cascade')
    result_id = fields.Many2one("mrp.operation.result", "Result")
    product_id = fields.Many2one("product.product", "Product")
    product_qty = fields.Float("Qty")
    product_uom = fields.Many2one("uom.uom","UoM")
    

class wizard_stock_picking(models.TransientModel):
    _inherit = "wizard.stock.picking"
    
    def prepare_stock_move_line(self, picking):
        vals = super(wizard_stock_picking, self).prepare_stock_move_line(picking)
        if picking.production_id:
            vals['material_id'] = self.production_id.id
        return vals
    
    
    