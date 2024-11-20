# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from datetime import datetime
import time
from datetime import timedelta
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"   
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import timedelta, datetime, date
    
class LotStackAllocation(models.Model):
    _inherit = 'lot.stack.allocation'
    
    license_id = fields.Many2one('ned.certificate.license', string="License Number", readonly=False)
    certificate_id = fields.Many2one(related='license_id.certificate_id', string='Certificate', readonly=True, store=True)
    license_type = fields.Selection(related='license_id.type', string='Type', store=True)
    
    @api.onchange("license_id", 'certificate_id', 'lot_id', 'delivery_id')
    def onchange_delivery_id(self):
        for this in self:
            if this.license_id:
                this.certificate_id = this.license_id.certificate_id.id
                this.license_type = this.license_id.type
            if this.lot_id and this.delivery_id:
                this.lot_id.nvs_id = this.delivery_id.contract_id.id
