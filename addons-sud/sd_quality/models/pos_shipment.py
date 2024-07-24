# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from datetime import datetime

    
class PostShipMentLine(models.Model):
    _inherit = "post.shipment.line"
    
    lot_id = fields.Many2one('lot.kcs', string='Lot Manager')
    lot_ned = fields.Char(related='lot_id.lot_ned', string='Lot Ned',store =True)
        