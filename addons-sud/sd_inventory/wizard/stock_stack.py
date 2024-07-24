# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import format_date, formatLang

from collections import defaultdict
from itertools import groupby
import json
import time

class CreateStockStack(models.TransientModel):
    _name = 'create.stock.stack'
        
    zone_id = fields.Many2one('stock.zone', string='Zone',)
    name = fields.Char('Stack name')
    date = fields.Date('Date')
    province_id = fields.Many2one('res.country.state', string='Province',)
    districts_id= fields.Many2one('res.district', 'Source', ondelete='restrict')
    hopper =fields.Boolean(string="hopper")
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse',)
    
    stack_type = fields.Selection([
        ('pallet', 'Pallet'),
        ('stacked', 'Stacked'),
        ('pile', 'Pile'),
        ('jum_1', 'Jum-1.0'),
        ('jum_1_3', 'Jum-1.3'),
        ('jum_1_5', 'Jum-1.5'),
        ('stack_wip', 'Stack Wip'),
        ('hp', 'Hopper')
    ],
    string='Stack type', default='stacked')
    
    _defaults = {
        'date': time.strftime('%Y-%m-%d')
    }
    @api.model
    def default_get(self, fields):
        res = {}
        vars=[]
        active_id = self._context.get('active_id')
        if active_id:
            move = self.env['stock.move.line'].browse(active_id)
            pick_info = move.picking_id
            res = {'districts_id':pick_info.districts_id and pick_info.districts_id.id or False,'warehouse_id': pick_info.warehouse_id.id,'zone_id':move.zone_id and move.zone_id.id or False}
        return res
    
    def create_stack(self):
        move_line_id = self._context.get('active_id')
        move = pick_info = self.env['stock.move.line'].browse(move_line_id)
        pick_info = move.picking_id
        stack_id = False
        # if pick_info.pcontract_id:
        #     stack_id = pick_info.pcontract_id.wr_line and pick_info.pcontract_id.wr_line or False
        for this in self:
            #Get name
            # if self.hopper:
            #     name = self.env['ir.sequence'].next_by_code('stock.stack.hopper.seq') or 'New'
            # else:
            #     name = self.env['ir.sequence'].next_by_code('stock.sack.seq') or 'New'
            var = {
                    'product_id':move.product_id.id,
                    'company_id':pick_info.company_id.id,
                    'zone_id':this.zone_id.id,
                    #'hopper':this.hopper or False,
                    'date':this.date,
                    'name':'/',
                    'stack_type':this.stack_type,
                    'districts_id':this.districts_id.id or False,
                    'p_contract_id': pick_info.pcontract_id and pick_info.pcontract_id.id or 0,
                    'warehouse_id':pick_info.warehouse_id and pick_info.warehouse_id.id or False
                  }
            if pick_info.warehouse_id.x_is_bonded:
                var.update({'is_bonded': True})
            if not stack_id:
                stack_id = self.env['stock.lot'].create(var)
            
            move.lot_id = stack_id and stack_id.id or False
            move.zone_id = this.zone_id.id
            if pick_info.pcontract_id:
                pick_info.pcontract_id.wr_line = stack_id
        return True



    