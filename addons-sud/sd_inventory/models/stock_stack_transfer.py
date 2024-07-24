# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from odoo.tools import float_round
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

from datetime import datetime
import time
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%d-%m-%Y"
DAT= "%Y-%m-%d"




class StockStack(models.Model):
    _name = "stock.stack.transfer"
    _order = 'create_date desc, id desc'
    _description = "Stock Stack Transfer"
     
    name = fields.Char(string='Description', required=True, size=128, readonly=True, states={'draft': [('readonly', False)]})
    from_zone_id = fields.Many2one('stock.zone', string='From Zone', ondelete='cascade', copy=False, readonly=True, states={'draft': [('readonly', False)]})
    to_zone_id = fields.Many2one('stock.zone', string='To Zone', ondelete='cascade', copy=False, readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection(selection=[('draft', 'New'), ('approved', 'Approved')],
         readonly=True, copy=False , default='draft')
    
    stack_id = fields.Many2one('stock.lot', string='Stack')
    net_weight = fields.Float(string='Net Weight')
    no_of_bag = fields.Float(string='Packing')
    note = fields.Text(string='Note', required=False,  readonly=True, states={'draft': [('readonly', False)]})
    
    date_order = fields.Date(string='Date', default=fields.Datetime.now, readonly=True, states={'draft': [('readonly', False)]})
    date_approve = fields.Date('Date Approval', readonly=True, copy=False,)
    user_approve_id = fields.Many2one('res.users', string='User Approve', readonly=True)
    user_responsible_id = fields.Many2one('res.users', 'Responsible', default=lambda self: self._uid, readonly=True)
    
    stack_ids = fields.Many2many('stock.lot', 'transfer_stack_rel', 'transfer_id', 'lot_id', string='Stack', readonly=True, states={'draft': [('readonly', False)]})
    
    @api.onchange('stack_id')
    def onchange_stack_id(self):
        for record in self:
            if record.stack_id:
                record.net_weight = record.stack_id.init_qty or 0
                record.no_of_bag = record.stack_id.bag_qty or 0
                record.name = record.stack_id.product_id.name
                record.from_zone_id = record.stack_id.zone_id and record.stack_id.zone_id.id or 0
                # record.stack_ids = [record.stack_id.id]
    
    def button_approved(self):
        for lock in self:
            # for stack in lock.stack_ids:
            #     stack.zone_id = lock.to_zone_id.id
            lock.stack_id.zone_id = lock.to_zone_id.id
            self.write({'state': 'approved', 'user_approve_id': self.env.uid,
                    'date_approve': datetime.now()})
    
    
    
