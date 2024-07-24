# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"    

    
    
class NpeNvpRelation(models.Model):
    _name = "npe.nvp.relation"
    
    @api.depends('npe_contract_id','contract_id')
    def _total_deposit_amount(self):
        for relation in self:
            deposit_amount = 0.0
            if relation.npe_contract_id:
                for line in relation.npe_contract_id.request_payment_ids:
                    deposit_amount += line.total_payment
                relation.deposit_amount = deposit_amount
    
    @api.depends('npe_contract_id','contract_id')
    def _origin_qty(self):
        for relation in self:
            origin_qty = 0.0
            if relation.npe_contract_id:
                for line in relation.npe_contract_id.contract_line:
                    origin_qty +=line.product_qty
                relation.origin_qty = origin_qty
    
    deposit_amount = fields.Float(compute='_total_deposit_amount',string = 'Deposit Amount')
    npe_contract_id = fields.Many2one('purchase.contract', string='NPE')
    contract_id = fields.Many2one('purchase.contract', string='NVP')
    product_qty = fields.Float('Fixed Qty',digits=(16, 0))
    origin_qty = fields.Float(compute='_origin_qty',string = 'Original Qty',digits=(16, 0))
    type = fields.Selection([('fixed', 'Fixed'), ('temporary', 'Temporary')], string='Type',
                     readonly=True,store= True)
    
    ##### PTBF NED CONTRACT  #########################################################################
    
    qty_received = fields.Float(related='npe_contract_id.qty_received',  string='Received')
    rate = fields.Float(string='Rate')
    ptbf_id = fields.Many2one('ptbf.fixprice',string='Ptbf fixprice',)
    price_fix = fields.Float(related='ptbf_id.price_fix',string="Price Fix")
    name_ptbf = fields.Char(related='ptbf_id.name',string="Name")
    
    ##### END PTBF NED CONTRACT  #########################################################################

    ##### NED CONTRACT  #########################################################################
    
    total_qty_fixed = fields.Float(related='npe_contract_id.total_qty_fixed',  string='Total Fixed Qty' ,store=True)
    qty_unfixed = fields.Float(related='npe_contract_id.qty_unfixed',  string='UnFixed', store= True)
    #date_fixed = fields.Date(related='contract_id.date_order',  string='Date Fixed',store=True)
    original_npe_qty = fields.Float(related='npe_contract_id.total_qty',  string='Original NPE', store= True)
    partner_id = fields.Many2one(related='npe_contract_id.partner_id',  string='Supplier',store=True)
    product_id = fields.Many2one(related='npe_contract_id.product_id',  string='Product',store=True)
    qty_unreceived = fields.Float(related='npe_contract_id.qty_unreceived',  string='UnReceived', store= True )
    relation_price_unit = fields.Float(related='contract_id.contract_line.price_unit', string='Fixed Price', store= True)
    date_fixed = fields.Date(string='Date Fixed',default= time.strftime(DATE_FORMAT))
    
    # date_tz = fields.Date(compute='_compute_date',string = "date", store=True)
    # day_tz = fields.Char(compute='_compute_date',string = "Month", store=True)
    ##### END PTBF NED CONTRACT  #########################################################################

    