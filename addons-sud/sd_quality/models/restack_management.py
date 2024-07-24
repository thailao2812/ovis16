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


class RestackManagement(models.Model):
    _name = "restack.management"

    name = fields.Char(string='Lot No')
    date_request = fields.Date(string='Date of Request', default=fields.Date.context_today)
    finished_date = fields.Date(string='Finished Date', default=fields.Date.context_today)
    date_export = fields.Date(string='Date Export', default=datetime.now().date())
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse',
                                   domain="[('code', 'in', ['KTN-AP-B', 'KTN-AP-N', 'KTN-LT-B', 'KTN-LT-N', 'CWT'])]")
    
    traffic_contract = fields.Many2one('traffic.contract', string='S Contract')
    
    x_p_contract_name = fields.Char('P Contract', size=10000)
    x_p_contract_ids = fields.Many2many('s.contract', 'restack_management_s_contract_rel', 'restack_management_id',
                                        's_contract_id', 'P Contract')
    stack_no = fields.Many2many('stock.lot', 'restack_management_stock_stack_rel', 'restack_management_id',
                                'stock_stack_id', string='Stack No.')
    partner_id = fields.Many2one('res.partner', string='Customer')
    buyer_ref = fields.Char(string='Buyer Ref')
    product_id = fields.Many2one('product.product', string='Product')
    packing_id = fields.Many2one('ned.packing', string='Packing')
    quantity = fields.Float(string='GDN Net Qty')
    balance_net = fields.Float(string='Balance Net')
    payment = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done')
    ], string='Payment Status', default='draft')
    remark = fields.Char(string='Remark')
    status = fields.Selection([
        ('pending', 'Pending'),
        ('done', 'Done')
    ], string='State', default='pending')
    storing_days = fields.Float(string='Storing Days')
    qty_per_contain = fields.Float(string='Qty Per Container(mts)')
    qty_request = fields.Float(string='Qty Request')
    goods_status = fields.Char(string='Goods Status')
    type = fields.Selection([
        ('restack', 'Re-Stack'),
        ('rebagging', 'Re-Bagging')
    ], string='Type', default='restack')
    
    #err
    # @api.onchange('traffic_contract')
    # def onchange_traffic_contract(self):
    #     for record in self:
    #         if record.traffic_contract:
    #             record.x_p_contract_name = record.traffic_contract.x_p_contract_link or ''
    #             record.partner_id = record.traffic_contract.partner_id and record.traffic_contract.partner_id.id or False
    #             record.product_id = record.traffic_contract.standard_id and record.traffic_contract.standard_id.id or False
    #             record.packing_id = record.traffic_contract.packing_id and record.traffic_contract.packing_id.id or False

    def button_confirm(self):
        for record in self:
            record.write({
                'status': 'done'
            })

    def button_confirm_payment(self):
        for record in self:
            record.write({
                'payment': 'done'
            })

    @api.onchange('qty_request', 'quantity')
    def onchange_balance_net(self):
        self.balance_net = self.qty_request - self.quantity


    @api.onchange('finished_date', 'date_export')
    def onchange_storing_days(self):
        if self.finished_date and self.date_export:
            # self.storing_days = (datetime.strptime(self.date_export, '%Y-%m-%d') -
            #                      datetime.strptime(self.finished_date, '%Y-%m-%d')).days
            
            self.storing_days = (self.date_export - self.finished_date).days
            


    @api.model
    def update_data_restack_management(self):
        restack_full = self.env['restack.management'].search([])
        for re in restack_full:
            # re.storing_days = (datetime.strptime(re.date_export, '%Y-%m-%d') -
            #                      datetime.strptime(re.finished_date, '%Y-%m-%d')).days
            
            re.storing_days = (re.date_export - re.finished_date).days
                                 
                                 
        return True
