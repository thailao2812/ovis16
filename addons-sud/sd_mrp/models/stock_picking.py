# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from datetime import datetime
import time
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%d-%m-%Y"
DATE_FORMAT = "%Y-%m-%d"
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime, timedelta


class StockPicking(models.Model):
    _inherit = "stock.picking"
    
    mrp_note = fields.Text(related="production_id.notes", store = True, string="Mrp notes")
    processing_loss_aproval_id =fields.Many2one('processing.loss.aproval', string="Loss Approved")
    
    def button_sd_validate(self):
        pick = self
        if pick.picking_type_id.code =='production_in' and pick.product_id.pass_kcs_for_loss == True:
            if not self.env['processing.loss.aproval'].sudo().search([('picking_id','=',pick.id)]):
                raise UserError(_('Please Create Processing loss before done this GRP - %s')%(pick.name))
        res = super(StockPicking,self).button_sd_validate()
        return res
    
    def create_processing_loss_aproval(self):
        for pick in self:
            if pick.picking_type_id.code =='production_in' and pick.product_id.categ_id.code =='Loss':
                if self.env['processing.loss.aproval'].sudo().search([('picking_id','=',pick.id)]):
                    return True
                pick.processing_loss_aproval_id = self.env['processing.loss.aproval'].sudo().create({'production_id':pick.production_id.id,
                                                                   'weight_loss':pick.total_init_qty,
                                                                   'picking_id':pick.id})