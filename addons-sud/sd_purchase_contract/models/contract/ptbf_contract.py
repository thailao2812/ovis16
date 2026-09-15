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


    
class PurchaseContract(models.Model):
    _inherit = "purchase.contract"

    ptbf_ids = fields.One2many('ptbf.fixprice','contract_id',string="PTBF")
    date_fix = fields.Date(string='Reference Price Month')
    rolling_ids = fields.One2many('ptbf.rolling.month','contract_id',string="PTBF")
    
    appendix_ids = fields.One2many('appendix.ptbf','ptbf_id',string="Appendix")
    contract_p_id = fields.Many2one('s.contract', string="PNo")
    month_code = fields.Char(compute='_get_month_code_intenational', string='Month', store = True)
    diff_price = fields.Float(compute='_get_diff_price', string='Diff.', store = True)
    payment_term_item = fields.Text(string="Other Payment term")

    @api.depends('contract_line.diff_price','rolling_ids.diff_price')
    def _get_diff_price(self):
        for line in self:
            if line.contract_line:
                diff_price = line.contract_line[0].diff_price
                if line.rolling_ids:
                    diff_price = line.rolling_ids.sorted(key=lambda l: l.date,reverse=True)[0].diff_price
                line.diff_price = diff_price
            return diff_price
    
    fixed_vnd = fields.Float(string="Fixed VNĐ" , compute='get_qty_allocate', store = True)
    qty_allocate = fields.Float(string="Qty Allocate" , compute='get_qty_allocate', store = True)
    
    @api.depends('ptbf_ids','ptbf_ids.quantity_receive','ptbf_ids.quantity_fixed','state', 'qty_received')
    def get_qty_allocate(self):
        qty_allocate = 0
        for i in self:
            qty_allocate = 0
            fixed_vnd = 0
            for line in i.ptbf_ids:
                qty_allocate += line.quantity_receive
                fixed_vnd += line.quantity_fixed
            i.qty_allocate = i.qty_received - qty_allocate
            i.fixed_vnd = fixed_vnd
            
    
    
    sd_price = fields.Float(string='SD')
    si_price = fields.Float(string='SI')
    # 6/12 Thai Lao
    cert_cost = fields.Float(string='Cert Cost')
        
    # total_payment = fields.Float(related='request_payment_ids.total_payment', string='Total Payment')
    # SON create price converted method
    # @api.depends('type_price_weight','total_qty','input_centlb')
    # def _weight_converted(self):
    #     for this in self:
    #         if this.type_price_weight == 'vndkg':
    #              this.price_converted = input_centlb * 507.06
    #         if this.type_price_weight == 'vndmts':
    #              this.price_converted = input_centlb * 507063
    #         if this.type_price_weight == 'usdmts':
    #              this.price_converted = input_centlb * 22.0462
    #         if this.type_price_weight == 'centlb':
    #              this.price_converted = input_centlb * 1

    # price_converted = fields.Float(compute='_price_converted', string="Price Converted", readonly=True, store=True, default=0.0000, digits=(16, 2))    


    @api.depends('date_fix', 'rolling_ids.date_fixed')
    def _get_month_code_intenational(self):
        for line in self:
            date = False
            if line.date_fix:
                date = line.date_fix or False
                
            for i in line.rolling_ids:
                date = i.date_fixed
                
            if date:
                # date = datetime.strptime(date, DATE_FORMAT)
                year = str(date.year)[2:4]
                date = date.strftime('%m')
                
                if date in ('01', '02'):
                    line.month_code = year + 'F'
                elif date in ('03', '04'):
                    line.month_code = year + 'H'
                elif date in ('05', '06'):
                    line.month_code = year + 'K'
                elif date in ('07', '08'):
                    line.month_code = year + 'N'
                elif date in ('09', '10'):
                    line.month_code = year + 'U'
                elif date in ('11', '12'):
                    line.month_code = year + 'X'
            else:
                line.month_code = ''

    @api.depends('request_payment_ids','request_payment_ids.total_payment')
    def _get_total_payment(self):
        for i in self:
            total_payment = 0
            for line in i.request_payment_ids:
                total_payment += line.total_payment
            i.total_payment = total_payment

    total_payment = fields.Float(compute='_get_total_payment', string='Total Payment', store = True, digits=(12, 0))
        
    
    def _get_printed_report_name(self):
        self.ensure_one()
        if self.type == 'ptbf':
            report_name = (_('%s')%( self.name))
        elif self.type == 'consign':
            report_name = (_('%s')%(self.name))
        else:
            report_name = (_('%s')%(self.name))
        return report_name
    
            
    def print_contract_ptbf(self):
        self.print_count += 1
        if self.nvp_ids:
            return self.env.ref(
                'sd_purchase_contract.report_contract_ptbf_npe').report_action(self)
            
        else:
            return self.env.ref(
                'sd_purchase_contract.report_contract_ptbf').report_action(self)
            

    def print_contract_ptbf_special(self):
        self.print_count += 1
        if self.nvp_ids:
            return {
                'type': 'ir.actions.report.xml',
                'report_name':'report_contract_ptbf_npe8',
                }
        else:
            return {
                    'type': 'ir.actions.report.xml',
                    'report_name':'report_contract_ptbf_report8',
                    }
    
    def allocate_recevice_qty(self):
        qty_allocate = self.qty_allocate
        if qty_allocate ==0:
            return
        
        for i in self.env['ptbf.fixprice'].search([('contract_id','=',self.id)],order ='date_fix'):
            qty_allocate =self.qty_allocate
            for j in i.history_rate_ids:
                quantity_receive = 0
                if j.qty_receive == j.qty_price:
                    continue
                if qty_allocate ==0:
                    continue
                
                if qty_allocate > j.qty_price - j.qty_receive:
                    quantity_receive =  j.qty_price - j.qty_receive
                    j.qty_receive += quantity_receive
                    qty_allocate -= quantity_receive
                else:
                    j.qty_receive += qty_allocate
                    qty_allocate -= qty_allocate

class AppendixPtbf(models.Model):
    _name = "appendix.ptbf"
    
    name = fields.Char(string="Name")
    date_order = fields.Date(string="Date")
    ptbf_id = fields.Many2one('purchase.contract',string="Contract")
    
    quantity = fields.Float(string="Quantity")
    liffe_price = fields.Float(string="Liffe Price")
    differencial = fields.Float(string="Differencial")
    exchange_rate= fields.Float(string="Exchange rate (provisional)")
    
    def compute_advanced_price(self):
        for i in self:
            i.advanced_price = round((i.liffe_price +i.differencial) * 70/100,0)
            i.advanced_price_vn = round((i.liffe_price +i.differencial) * 70/100 * i.exchange_rate/1000,0)
            i.payment_amount = round(i.advanced_price_vn  * i.quantity,0)
            
    advanced_price= fields.Float(string="Advanced price", compute='compute_advanced_price')
    advanced_price_vn = fields.Float(string="Advanced price", compute='compute_advanced_price')
    payment_amount = fields.Float(string="Payment amount", compute='compute_advanced_price')
    
    def print_appendix_ptbf(self):
        return self.env.ref(
                'sd_purchase_contract.report_appendix_ptbf_report').report_action(self)
    
    def _get_printed_report_name(self):
        self.ensure_one()
        return 'Appendix ptbf'      
                
    
class PtbfFixPrice(models.Model):
    _name = "ptbf.fixprice"
    
    def _get_printed_report_name(self):
        self.ensure_one()
        return 'fixprice'
    
    def name_get(self):
        result = []
        for record in self:
            name = record.date_fix
            result.append((record.id, name))
        return result
    
    def print_ptbf(self):
        return self.env.ref(
                'sd_purchase_contract.report_ptbf_report_fix_price').report_action(self)
    
                

    def get_differencial_price(self):
        for record in self:
            if record.contract_id.rolling_ids:
                return record.contract_id.rolling_ids.sorted(key=lambda r: r.date_rolling, reverse=True)[0].diff_price
            else:
                return record.contract_id.contract_line[0].diff_price
    
    # def print_ptbf(self):
    #     return {
    #             'type': 'ir.actions.report.xml',
    #             'report_name':'report_ptbf_report',
    #             }
    
    def unlink(self):
        for i in self.history_rate_ids:
            if i.grn_id:
                raise UserError(_('You don\'t delete !!!'))
        return super(PtbfFixPrice, self).unlink()
    
    no = fields.Char(string="No.")
    contract_id = fields.Many2one('purchase.contract',string="PTBF")
    product_id = fields.Many2one(related='contract_id.product_id',string='Product',store =True)
    date_fix = fields.Date(string="Date Fix")
    name = fields.Char(string="Description")
    quantity = fields.Float(string="Quantity")
    
    
    relation_ids = fields.One2many('npe.nvp.relation','ptbf_id',string="PTBF")
    history_rate_ids = fields.One2many('history.rate','history_id',string="Rate")
    
    
    #Kiet: hàm cũ đôi lại sau này
    # @api.depends('contract_id.contract_line.diff_price','price_fix','quantity','date_fix','contract_id.rolling_ids')
    # def _compute_final_price(self):
    #     for line in self:
    #         if line.contract_id and line.contract_id.contract_line:
    #             obj = line.contract_id.contract_line[0]
    #             line.final_price = line.price_fix + obj.diff_price
    #             if line.date_fix and line.contract_id.rolling_ids.filtered(lambda x: x.date_rolling <= line.date_fix):
    #                 line.final_price = line.price_fix + line.contract_id.rolling_ids.sorted(key=lambda l: l.date_rolling,reverse=True).filtered(lambda x: x.date_rolling <= line.date_fix)[0].diff_price
    #             line.total_amount = line.quantity/1000 * line.price_fix
    
    @api.depends('contract_id.contract_line','contract_id.contract_line.diff_price','contract_id.rolling_ids','contract_id.rolling_ids.diff_price','price_fix')
    def _compute_final_price(self):
        for line in self:
            if line.contract_id:
                diff = line.contract_id._get_diff_price()
                line.diff = diff
                line.final_price = line.price_fix + diff

    final_price = fields.Float(string="Final Price",compute='_compute_final_price',store = True)
    price_fix = fields.Float(string="Price Fix")
    diff = fields.Float(string="Diff", compute='_compute_final_price',store = True)
    
    
    total_amount = fields.Float(string="Total Amount")

    total_amount_final = fields.Float(string="Total Amount", compute='_compute_total_amount_final', store=True, digits=(12, 0))

    @api.depends('history_rate_ids', 'history_rate_ids.total_amount_vn')
    def _compute_total_amount_final(self):
        for record in self:
            record.total_amount_final = sum(i.total_amount_vn for i in record.history_rate_ids)

    
    # SON create type_price_weight
    input_centlb = fields.Float(string="Currency", default=1.0000, digits=(16, 0))
    
#     @api.multi
#     def get_qty_fix(self):
#         for i in self:
#             i.quantity_fixed =  sum(self.env['npe.nvp.relation'].search([('ptbf_id','=',i.id)]).mapped('product_qty'))
#             i.quantity_unfixed = i.quantity - i.quantity_fixed
    
    def compute_qty_receive(self):
        for i in self:
            receive = 0
            fixed = 0
            for j in i.history_rate_ids:
                receive += j.qty_receive
                fixed += j.qty_price
            i.quantity_receive = receive
            i.quantity_fixed = fixed
            i.quantity_unfixed = i.quantity - fixed
            
    quantity_receive = fields.Float(string="Receive Qty",compute='compute_qty_receive')
    quantity_fixed = fields.Float(string="Fixed Qty" ,compute='compute_qty_receive')
    quantity_unfixed = fields.Float(string="Qty Unfixed" , compute='compute_qty_receive')
    
    @api.model
    def create(self, vals):
        new_id = super(PtbfFixPrice, self).create(vals)
        new_id.product_id = new_id.contract_id.contract_line[0] and new_id.contract_id.contract_line[0].product_id.id
        return new_id


class PTBFRollingMonth(models.Model):
    _name = "ptbf.rolling.month"
    
    @api.onchange('date_fixed')
    def onchange_default_quantity(self):
        self.quantity = self.contract_id.qty_allocate - self.contract_id.total_qty_fixed
        
    no = fields.Char(string="No.")
    date_rolling = fields.Date(string='Date',default= datetime.now(),required =True)
    date_fixed = fields.Date(string='Reference Price Month',default= datetime.now(),required =True)
    diff_price = fields.Float(string='Differencial Price')   
    quantity = fields.Float(string='Quantity')
    contract_id = fields.Many2one('purchase.contract',string="PTBF")
    date = fields.Date(string='Fixation deadline',default= datetime.now(),required =True)
    
    def print_roll_ptbf(self):
        return {
                'type': 'ir.actions.report.xml',
                'report_name':'report_roll_ptbf',
                }

class HistoryRate(models.Model):
    _name = "history.rate"
    
    product_id = fields.Many2one('product.product',string="Product")
    uom_id = fields.Many2one(related ='product_id.uom_id',string="UoM")
    qty_price = fields.Float(string="Quantity Fixed")
    qty_receive = fields.Float(string="Quantity receive")
    
    rate = fields.Float(string="Rate")
    date_receive = fields.Date(string="Date Receive")
    history_id = fields.Many2one('ptbf.fixprice',string="History")
    ptbf_id = fields.Many2one('purchase.contract',string="Contract")
    final_price_en = fields.Float(string="Final Price (USD)")
    move_id = fields.Many2one('stock.move',string="Inventory")
    grn_id = fields.Many2one('stock.picking',string="Picking")
    
    
    @api.depends('rate','qty_price','qty_receive','final_price_en')
    def _compute_price(self):
        for line in self:
            line.final_price_vn = line.rate * line.final_price_en
            line.total_amount_en = line.qty_receive/1000 * line.final_price_en
            line.total_amount_vn = line.qty_receive/1000 * line.final_price_en * line.rate

    final_price_vn = fields.Float(string='Final Price VN')
    total_amount_en = fields.Float(string="Total (USD)")
    total_amount_vn = fields.Float(string="Total (VND)")
    
    def print_bien_ban_chot_gia(self):
        
        return self.env.ref(
            'sd_purchase_contract.report_ptbf_chot_gia').report_action(self)
            
