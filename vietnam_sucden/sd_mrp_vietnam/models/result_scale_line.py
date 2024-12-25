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
    
class MrpOperationResultScale(models.Model):
    _inherit = 'mrp.operation.result.scale'
    
    form_name = fields.Char(string='Form', compute='_compute_form_name', store=True)
    batch_name = fields.Char(string='Batch Name', compute='_compute_form_name', store=True)
    
    @api.depends('operation_result_id','picking_scale_id')
    def _compute_form_name(self):
        for rec in self:
            if rec.operation_result_id:
                rec.form_name = rec.operation_result_id.name
                rec.batch_name = rec.operation_result_id.production_id.name
            else:
                rec.form_name = rec.picking_scale_id.name
                rec.batch_name = rec.picking_scale_id.production_id.name
                