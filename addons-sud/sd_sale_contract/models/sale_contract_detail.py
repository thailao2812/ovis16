# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from datetime import datetime, date, timedelta, time
    
class SaleContractDetail(models.Model):
    _name = "sale.contract.deatail"

    confirm_date = fields.Datetime(string='Confirm Date')

    @api.onchange('p_contract_id')
    def onchange_pcontract(self):
        for record in self:
            if record.p_contract_id:
                record.shipper_id = record.p_contract_id.partner_id and record.p_contract_id.partner_id.id or 0
                record.product_id = record.p_contract_id.product_id and record.p_contract_id.product_id.id or 0
                record.scertificate_id = record.p_contract_id.certificate_id and record.p_contract_id.certificate_id.id or 0
                stk_id = self.env['stock.lot'].search([('p_contract_id', '=', record.p_contract_id.id)], limit=1)
                record.stack_id = stk_id and stk_id.id or 0
                record.warehouse_id = record.p_contract_id.warehouse_id and record.p_contract_id.warehouse_id.id or 0
                record.name = record.p_contract_id.p_contract_line_ids and record.p_contract_id.p_contract_line_ids[0].name or record.p_contract_id.p_quality

    def btn_approve(self):
        return self.write({
            'state': 'approve',
            'confirm_date': datetime.today()
        })
    
    
    name = fields.Char('Quality', size=256)
    p_contract_id = fields.Many2one('s.contract', 'P Contract')
    product_id = fields.Many2one('product.product', 'Product')
    shipper_id = fields.Many2one('res.partner', string='Shipper')
    scertificate_id = fields.Many2one('ned.certificate', string='Certificate')
    stack_id = fields.Many2one('stock.lot', string='WR No.')
    #err
    # x_stk_code = fields.Char(string="Stack", related ="stack_id.name", store =True)
    x_bag_qty = fields.Float('Balance Bags')
    x_gd_qty = fields.Float('Inspection Qty')
    
    allocated_qty = fields.Float('Allocated Qty')
    tobe_qty = fields.Float('Allocate Qty')
    tobe_bag = fields.Float('Bag Allocate')
    balance_qty = fields.Float('Balance Qty')
    p_qty = fields.Float('Qty', related='p_contract_id.p_qty')
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse')
    state = fields.Selection([('draft', 'Draft'), ('approve', 'Approve')], string='Status')
    sp_id = fields.Many2one('sale.contract', 'NVS')
    p_on_hand = fields.Float(string='P On Hand')
    stack_on_hand = fields.Char(string='Real Stack Export')
    
    @api.model
    def create(self, vals):
        res = super(SaleContractDetail, self).create(vals)
        for rc in res:
            if rc.sp_id.state == 'draft' and rc.stack_id:
                rc.stack_id.allocate_qty += rc.tobe_qty
        return res

    def write(self, vals):
        res = super(SaleContractDetail, self).write(vals)
        for rc in self:
            if rc.sp_id.state == 'draft' and rc.stack_id:
                sale_contract_detail = self.search([
                    ('sp_id.state', '=', 'draft'),
                    ('stack_id', '=', rc.stack_id.id),
                    ('id', '!=', rc.id)
                ])
                stock_stack = self.env['stock.lot'].browse(rc.stack_id.id)
                if sale_contract_detail:
                    stock_stack.allocate_qty = sum(i.tobe_qty for i in sale_contract_detail)
                    stock_stack.allocate_qty += rc.tobe_qty
                # if stock_stack:
                #     stock_stack.allocate_qty += rc.allocated_qty
            # if rc.sp_id.state != 'draft' and rc.stack_id:
            #     stock_stack = self.env['stock.lot'].browse(rc.stack_id.id)
            #     if stock_stack:
            #         stock_stack.allocate_qty -= rc.allocated_qty
                # self.env['stock.lot'].browse(rc.stack_id.id).write({'allocate_qty': 0})
        return res