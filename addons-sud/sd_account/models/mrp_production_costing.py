# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict
import re

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"


from lxml import etree
import base64
import xlrd


class CostingPremiumLine(models.Model):
    _name= 'costing.premium.line'
    _description = 'Costing Premium Line'  
    _order = 'id desc'
    
    collection_id = fields.Many2one('mrp.periodical.production.costing',string="Premium", required=False,ondelete='cascade', index=True)
    product_id = fields.Many2one('product.product',string="Product", required=True)
    product_uom = fields.Many2one('uom.uom',related='product_id.uom_id',string="UoM", required=False)
    
    premium = fields.Float(string='Prem/Disct')
    #price = fields.Monetary(string='Price',currency_field='company_currency_id')
    price = fields.Float(string='Price',digits=(12, 9))
    value = fields.Monetary(string='Value', compute="compute_values", currency_field='company_currency_id')
    #value = fields.Float(string='Value', compute="compute_values",digits=(12, 4))
    flag= fields.Boolean(string="Flag", default=False)
    
    cost_collection_id = fields.Many2one('mrp.production.order.cost.collection',string="Premium", required=False,ondelete='cascade', index=True)
    
    
    @api.depends('product_qty','value')
    def compute_values(self):
        for order in self:
            order.value = order.product_qty * order.price
    
    company_currency_id = fields.Many2one('res.currency', related='collection_id.company_currency_id', readonly=True)
    
    
                
    product_qty = fields.Float(string = 'Product Qty' ,digits=(12, 0))
    
    
    
class MrpPeriodicalProductionCosting(models.Model):
    _name= 'mrp.periodical.production.costing'
    _description = 'Periodical Production Costing'
    _order = 'id desc'
    
    name = fields.Many2one('account.period', 'Period', required=True, readonly=True, states={'draft':[('readonly',False)]})
    notes = fields.Text(string="Notes")
    production_order_ids = fields.Many2many('mrp.production', 'mo_periodical_production_costing_rel', 'periodical_costing_id', 'production_id', 'Production orders', required=False)
    #Thanh: Related Production Order Allocation
    mo_cost_collection_lines = fields.One2many('mrp.production.order.cost.collection', 'periodical_costing_id', 'Production Orders', readonly=True)
    premium_ids =fields.One2many('costing.premium.line', 'collection_id', 'Premium Orders', readonly=False)
    #Thanh: Group Factory Overhead Control
    #periodical_overhead_lines = fields.One2many('periodical.overhead', 'periodical_costing_id', 'Overhead Details'),
    
    premium_id = fields.Many2one('mrp.bom.premium', 'Premium', required=True, readonly=True, states={'draft':[('readonly',False)]})
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse', required=True, readonly=True, states={'draft':[('readonly',False)]})
    state = fields.Selection([
        ('draft','Draft'),
        ('posted','Posted'),
        ('done','Done'),
        ('cancel','Cancelled'),
        ],'Status',  readonly=True,default='draft')
    
    date_end = fields.Date(related='name.date_stop', readonly=True)
    
    #kiet: moi them
    direct_cost_lines = fields.One2many('mo.direct.cost.collection', 'cost_id', 'Direct costs', readonly=True)
    direct_materials_ids = fields.One2many('cost.materials.collection','cost_id',string='Direct Materials')
    direct_cost_ids = fields.One2many('mo.cost.direct', 'cost_id', 'Direct costs', readonly=True)
    
    file = fields.Binary('File', help='Choose file Excel')
    file_name =  fields.Char('Filename', readonly=True)
    
    total_cost = fields.Monetary(string='Total Cost',compute='_compute_values',store = True,currency_field='company_currency_id')
    currency_id = fields.Many2one('res.currency',default=3)
    
    
    # consumed_products_ids = fields.One2many('stock.move', 'consumed_id', 'Consumed Products', readonly=True)
    # produced_products_ids = fields.One2many('stock.move', 'produced_id', 'Produced Products', readonly=True)
    
    
    
    def dieuchinh_values(self):
        for this in self:
                
            for move in this.consumed_products_ids:
                move.entries_id.button_cancel()
                move.entries_id.unlink()
                move.state = 'draft'
                move.unlink()
#             
    
    def fifo_reopen_fifo(self,move_ids):
        for move in self.env['stock.move'].browse(move_ids):
            move.remove_fifo()
            
    def post_done(self):
#         for line in self.consumed_products_ids:
#             if not line.entries_id:
#                 self.get_entries(line)
        
        for line in self.produced_products_ids:
            if not line.entries_id:
                self.get_entries(line)
#             if line.entries_id:
#                 line.entries_id.button_cancel()
#                 line.entries_id.unlink()
    
    def cancel(self):
        for this in self:
            for input in this.consumed_products_ids:
                if input.entries_id:
                    input.entries_id.button_cancel()
                    input.entries_id.unlink()
                input.action_cancel()
                input.unlink()
            
            for output in this.produced_products_ids:
                if output.entries_id:
                    output.entries_id.button_cancel()
                    output.entries_id.unlink()
                output.action_cancel()
                output.unlink()
            this.state = 'draft'
        
    
    def fifo_nvl(self):
        for this in self.direct_materials_ids:
            this.fifo_nvl()
        return 1
    
    def update_fix(self):
        for this in self:
            flag= False
            try:
                recordlist = base64.decodestring(this.file)
                excel = xlrd.open_workbook(file_contents = recordlist)
                sh = excel.sheet_by_index(0)
            except e:
                raise UserError(_('Warning !!!'))
            if sh:
                for row in range(sh.nrows):
                    move_id = sh.cell(row,0).value or False
                    if isinstance(move_id, float):
                        move_id = int(move_id)
                    stack_id = sh.cell(row,1).value or False
                    
                    if isinstance(stack_id, float):
                        stack_id = int(stack_id)
                    
                    move_id = self.env['stock.move'].browse(move_id)
                    if not move_id.stack_id:
                        move_id.stack_id = stack_id
        return

    
    def import_price(self):
        for this in self:
            flag= False
            try:
                recordlist = base64.decodestring(this.file)
                excel = xlrd.open_workbook(file_contents = recordlist)
                sh = excel.sheet_by_index(0)
            except e:
                raise UserError(_('Warning !!!'))
            if sh:
                for row in range(sh.nrows):
                    if not flag:
                        flag= True
                        continue
                    
                    in_product_code = sh.cell(row,0).value or False
                    in_qty = sh.cell(row,1).value or False
                    out_product_code = sh.cell(row,2).value or False
                    out_qty = sh.cell(row,3).value or False
                    price = sh.cell(row,4).value or False
                    
                    in_product = self.env['product.product'].search([('default_code','=',in_product_code)])
                    if in_product and in_qty and in_qty !=0:
                        material = self.env['cost.materials.collection'].search([('product_id','=', in_product.id),('cost_id','=', this.id)],limit =1)
                        if material:
                            material.write({'fifo_net_qty':in_qty})
                        else:
                            var ={
                                'cost_id':this.id,
                                'product_id':in_product.id,
                                'state': 'draft',
                                'fifo_net_qty':in_qty
                            }
                            self.env['cost.materials.collection'].create(var)
                            
                    out_product = self.env['product.product'].search([('default_code','=',out_product_code)])
                    if out_product and out_qty and out_qty !=0:
                        premium = self.env['costing.premium.line'].search([('product_id','=', in_product.id),('collection_id','=', this.id)],limit =1)
                        if premium:
                            premium.write({'product_qty':out_qty,'price':price/1000})
                        else:
                            val ={
                                'collection_id':this.id,
                                'product_id':out_product.id,
                                'product_qty':out_qty,
                                'price':round(price/1000,5)
                                #'price':prem.premium +premium_id.premium
                                }
                            self.env['costing.premium.line'].create(val)
                    
    
    
    @api.depends('mo_cost_collection_lines')
    def compute_qty(self):
        for order in self:
            total_cost = 0.0
            for line in order.direct_materials_ids:
                total_cost += line.amount_fifo_qty or 0.0
            order.total_cost = total_cost
            
    total_cost = fields.Monetary(string = 'Total Cost',compute='compute_qty',currency_field ='company_currency_id')
    
    #total_cost = fields.Monetary(string = 'Total Cost',currency_field ='company_currency_id')
    
    company_id = fields.Many2one('res.company', string='Company', 
        required=False, readonly=True, states={'draft': [('readonly', False)]},
        default=lambda self: self.env['res.company']._company_default_get('mrp.periodical.production.costing'))
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)
    second_currency_id = fields.Many2one('res.currency', related='company_id.second_currency_id', readonly=True)
    
    
    
            
    def printf_mo(self):
        return self.env.ref(
            'sd_account.report_cost_productions').report_action(self)
    
    def _get_accounting_data(self, line):
        product_obj = self.env['product.template']
        accounts = product_obj.browse(line.product_id.product_tmpl_id.id).get_product_accounts()
        acc_valuation = accounts.get('stock_valuation', False)
        #Kiệt: Trường hợp xuất kho NVL
        if line.location_id.usage =='internal' and line.location_dest_id.usage == 'production':
            acc_dest = line.location_dest_id.valuation_in_account_id.id
            acc_src =  acc_valuation.id
        
        #Kiet: Trượng hợp nhập kho Thành phẩm
        if line.location_id.usage =='production' and line.location_dest_id.usage == 'internal':
            #Kiet: Nhập kho sản xuất 
            acc_dest = acc_valuation.id
            acc_src = line.location_id.valuation_out_account_id.id
            
        if not accounts.get('stock_journal', False):
            raise UserError(_('You don\'t have any stock journal defined on your product category, check if you have installed a chart of accounts'))
        journal_id = accounts['stock_journal'].id
        return journal_id, acc_src, acc_dest
    
    
    def _prepare_account_move_line(self,line, qty,  credit_account_id, debit_account_id):
        debit = credit = line.price_unit * qty
        partner_id = (line.picking_id.partner_id and self.pool.get('res.partner')._find_accounting_partner(line.picking_id.partner_id).id) or False
        name = line.product_id.default_code
        debit_line_vals = {
            'name': name,
            'product_id': line.product_id.id,
            'quantity': qty,
            'product_uom_id': line.product_id.uom_id.id,
            'partner_id': partner_id,
            'debit': debit or 0.0,
            'credit':  0.0,
            #'second_ex_rate':second_ex_rate or 0.0,
            #'amount_currency':amount_currency,
            'account_id': debit_account_id,
            #'currency_id': line.second_currency_id.id
        }
        credit_line_vals = {
            'name': name,
            'product_id': line.product_id.id,
            'quantity': qty,
            'product_uom_id': line.product_id.uom_id.id,
            'partner_id': partner_id,
            'debit': 0.0,  
            'credit': credit or 0.0,
            #'second_ex_rate':second_ex_rate or 0.0,
            #'amount_currency': (-1) * amount_currency,
            'account_id': credit_account_id,
            #'currency_id': line.second_currency_id.id
        }
        return [(0, 0, debit_line_vals), (0, 0, credit_line_vals)]
    
    #Kiet: Nghiep vu nhập kho NVL khi đã FIFO
    def get_entries(self,move_line):
        move_obj = self.env['account.move']
        
        journal_id, acc_src, acc_dest = self._get_accounting_data(move_line)
        move_lines = self._prepare_account_move_line(move_line, move_line.product_qty,  acc_src, acc_dest)
        ref = u'Giá thành ' + self.name.name 
        if move_lines:
            date = move_line.date
            new_move_id = move_obj.create({'journal_id': journal_id,
                                  'account_analytic_id':self.warehouse_id and self.warehouse_id.account_analytic_id.id,
                                  'line_ids': move_lines,
                                  'date': date,
                                  'ref': ref,
                                  'narration':False})
            try:
                new_move_id.post()
            except ex:
                print(move_line)
                
            move_line.entries_id = new_move_id.id
    
    
    
    def post(self):
        for this in self:
            for line in this.produced_products_ids:
                if line.fifo_qty != 0:
                    raise
# #             
#             for line in this.consumed_products_ids:
#                 line.action_cancel()
#                 if line.entries_id:
#                     line.entries_id.button_cancel()
#                     line.entries_id.unlink()
#                 line.unlink()
#                     
#                 
#             for line in this.produced_products_ids:
#                 line.action_cancel()
#                 line.unlink()
                  
                  
            origin = u'Giá thành tháng ' + this.name.name
            location_id = self.env['stock.location'].search([('code','=','NVP - BMT')])
#             Thành phẩm
            for premium in self.premium_ids:
                if not premium.product_qty and not premium.price and premium.price ==0:
                    continue
                data = {
                        'product_uom_qty':premium.product_qty,
                        'price_unit':premium.price,
                        'location_id':premium.product_id.property_stock_production.id or False,
                        'name': premium.product_id.default_code,
                        'date': this.name.date_stop,
                        'product_id': premium.product_id.id,
                        'product_uom': premium.product_id.uom_id.id, 
                        'location_dest_id': location_id.id,
                        'company_id': this.company_id.id,
                        'origin': origin, 
                        'produced_id':this.id,
                        'state': 'done'}
                move_id = self.env['stock.move'].create(data)
                self.get_entries(move_id)
                   
                #Bút toán giá nhập kho
             
            #NVL tiêu thụ
            for materials in self.direct_materials_ids:
                if not materials.fifo_qty:
                    continue
                for allocation in materials.allocation_ids:
                    data = {
                            'product_uom_qty':allocation.allocated_qty,
                            'price_unit':allocation.allocated_value,
                            'location_id':location_id.id,
                            'name': materials.product_id.default_code, 
                            'date': this.name.date_stop,
                            'product_id': materials.product_id.id,
                            'product_uom': materials.product_id.uom_id.id, 
                            'location_dest_id': materials.product_id.property_stock_production.id or False, 
                            'company_id': this.company_id.id,
                            'origin': origin,
                            'consumed_id':this.id,
                            'state': 'done'}
                    move_id = self.env['stock.move'].create(data)
                    if move_id.price_unit:
                        self.get_entries(move_id)
                    
                    move_fifo = self.env['stock.move.fifo'].search([('fifo_colletion_id','=',allocation.id)])
                    if move_fifo:
                        move_fifo.fifo_out_id = move_id.id
                    else:
                        val ={
                              'fifo_id':allocation.from_move_id.id,
                              'product_qty':allocation.allocated_qty,
                              'fifo_colletion_id':allocation.id,
                              'out_qty':allocation.allocated_qty,
                              'fifo_out_id':move_id.id
                        }
                        fifo_id = self.env['stock.move.fifo'].create(val)
                    
            
            this.state = 'posted'
    
    def compute_cost(self):
        for this in self:
            #Xoá data làm lại
            sql='''
                DELETE FROM mo_direct_cost_collection where cost_id = %s;
                DELETE FROM cost_materials_collection where cost_id = %s;
                DELETE FROM mo_cost_direct where cost_id = %s;
                DELETE FROM costing_premium_line where collection_id = %s
            '''%(this.id,this.id,this.id,this.id)
            self.env.cr.execute(sql)
            
        #kiet: Lấy Lệnh sản xuất:
            mrp_ids = []
            sql ='''
                SELECT id 
                FROM mrp_production 
                WHERE state ='done'
                    and date(timezone('UTC',date_planned_start::timestamp)) between '%s' and '%s'
            '''%(this.name.date_start,this.name.date_stop)
            self.env.cr.execute(sql)
            for i in self.env.cr.dictfetchall():
                mrp_ids.append(i['id'])
            this.write({'production_order_ids':[[6,0,mrp_ids]]})
        #kiet: Lay thanh pham:
            sql ='''
                SELECT distinct sm.product_id 
                FROM stock_move_line  sm 
                    join stock_picking sp on sm.picking_id = sp.id
                    join stock_picking_type spt on sp.picking_type_id = spt.id
                where finished_id in (%s)
                    and sp.state ='done'
                    and qty_done !=0
                    and spt.code = 'production_in'
                    and init_qty !=0
            '''%(','.join(map(str, mrp_ids)))
            self.env.cr.execute(sql)
            for i in self.env.cr.dictfetchall():
                var ={
                    'cost_id':this.id,
                    'product_id':i['product_id'],
                }
                new_id = self.env['mo.direct.cost.collection'].create(var)
                
        # Kiet Tong gop cac GRP
                sql='''
                    SELECT sm.id move_id, qty_done, init_qty
                    FROM stock_move_line  sm 
                    join stock_picking sp on sm.picking_id = sp.id
                    join stock_picking_type spt on sp.picking_type_id = spt.id
                    where finished_id in  (%s)
                        and sp.state ='done'
                        and qty_done !=0
                        and spt.code = 'production_in'
                        and init_qty !=0
                        and sm.product_id = %s
                '''%(','.join(map(str, mrp_ids)),i['product_id'])
                self.env.cr.execute(sql)
                for i in self.env.cr.dictfetchall():
                    varl ={
                        'move_id':i['move_id'],
                        'fin_id':new_id.id,
                        'product_qty': i['qty_done'],
                        'init_qty':i['init_qty']
                    }
                    self.env['cost.finishs.details'].create(varl)
        
        #Kiet: Lay Nguyen vat lieu
            sql ='''
                SELECT distinct sm.product_id 
                FROM stock_move_line  sm 
                join stock_picking sp on sm.picking_id = sp.id
                join stock_picking_type spt on sp.picking_type_id = spt.id
                where material_id in (%s)
                    and sp.state ='done'
                    and spt.code = 'production_out'
                    and qty_done !=0
                    and init_qty !=0
            '''%(','.join(map(str, mrp_ids)))
            self.env.cr.execute(sql)
            for i in self.env.cr.dictfetchall():
                var ={
                    'cost_id':this.id,
                    'product_id':i['product_id'],
                    'state': 'draft',
                }
                new_id = self.env['cost.materials.collection'].create(var)
                
                # Kiet Tong gop cac GIP
                sql='''
                    SELECT sm.id move_id
                    FROM stock_move_line  sm
                    join stock_picking sp on sm.picking_id = sp.id
                    join stock_picking_type spt on sp.picking_type_id = spt.id
                    where material_id in  (%s)
                        and sp.state ='done'
                        and qty_done !=0
                        and init_qty !=0
                        and spt.code = 'production_out'
                        and sm.product_id = %s
                '''%(','.join(map(str, mrp_ids)),i['product_id'])
                self.env.cr.execute(sql)
                for i in self.env.cr.dictfetchall():
                    varl ={
                        'move_id':i['move_id'],
                        'material_id':new_id.id,
                    }
                    self.env['cost.materials.details'].create(varl)
                
                #new_id.fifo_allocation()
                
        
        #Kiet: Tạo bảng tính giá thành
            for prem in this.premium_id.prem_ids:
                # this.standard_cost = this.premium_id.standard_cost or 0.0
                premium_id = self.env['mrp.bom.premium.line'].search([('flag','=',True)],limit=1)
                produced_qty = 0.0
                # sql ='''
                #     SELECT sum(produced_qty) produced_qty 
                #     FROM mo_direct_cost_collection this where cost_id in (%s)
                #         and product_id = %s
                #     GROUP BY product_id
                #     HAVING sum(produced_qty) >0
                # '''%(this.id,prem.product_id.id)
                # self.env.cr.execute(sql)
                # for y in self.env.cr.dictfetchall():
                #     produced_qty = y['produced_qty'] or 0.0
                    
                val ={
                    'collection_id':this.id,
                    'product_id':prem.product_id.id,
                    'product_qty':produced_qty,
                    'premium':prem.premium or 0.0,
                    #'price':prem.premium +premium_id.premium
                    }
                self.env['costing.premium.line'].create(val)
            
# 
class MrpProductionOrderCostCollection(models.Model):
    _name= 'mrp.production.order.cost.collection'
    _description = 'Production Order Cost Collection'
    _order = 'id desc'
 
    name = fields.Many2one('mrp.production', 'Production order', required=False )
    #warehouse_id = fields.Many2one(related='name.warehouse_id', string="Warehouse")
    
    period_id = fields.Many2one(related='periodical_costing_id.name', string="Period")
    warehouse_id = fields.Many2one(related='name.warehouse_id', string="Warehouse",store= True)
    date_finished = fields.Datetime(related='name.date_finished', string="Date Finished",store= True)
    
    direct_cost_lines = fields.One2many('mo.direct.cost.collection', 'cost_collection_id', 'Direct costs', readonly=True)
    direct_materials_ids = fields.One2many('cost.materials.collection','collection_id',string='Direct Materials')
    direct_cost_ids = fields.One2many('mo.cost.direct', 'collection_id', 'Direct costs', readonly=True)
#     overhead_absorbed_lines = fields.One2many('mo.overhead.absorbed', 'cost_collection_id', 'OH absorbed', readonly=True)
    periodical_costing_id = fields.Many2one('mrp.periodical.production.costing', 'Related Periodical Costing',ondelete='cascade')
    date_approve = fields.Date(string="Date Approve",default=fields.Datetime.now)
    state = fields.Selection([
        ('draft','Draft'),
        ('posted','Posted'),
        ('cancel','Cancelled'),
        ],'Status',  readonly=True)
    
    company_currency_id = fields.Many2one('res.currency', related='periodical_costing_id.company_currency_id', readonly=True)
    premium_ids =fields.One2many('costing.premium.line', 'cost_collection_id', 'Premium Orders', readonly=False)
    
    
    @api.depends('direct_cost_ids','direct_materials_ids.value','direct_materials_ids','standard_cost')
    def _compute_values(self):
        for this in self:
            cost = 0
            product_qty = 0.0
            materials_cost = 0.0
            other_cost = 0.0
            for line in this.direct_materials_ids:
                cost += line.value
                materials_cost += line.value
                if line.product_id.flag_standard_cost:
                    product_qty += line.product_qty or 0.0
            
            for line in this.direct_cost_ids:
                cost +=  line.total_consume
                other_cost +=  line.total_consume
            
            standard_cost = this.standard_cost and this.standard_cost * product_qty /1000  or 0.0
            this.total_cost = cost + standard_cost
            this.materials_cost = materials_cost
            this.other_cost = other_cost
            
    total_cost = fields.Float(string='Total Cost',compute='_compute_values',store = True)
    currency_id = fields.Many2one('res.currency',default=3)
    
    standard_cost = fields.Float(string='Standard Cost',currency_field='company_currency_id', default=16.35)
    materials_cost = fields.Float(string='Material Cost',compute='_compute_values',store = True )
    other_cost = fields.Float(string='Other costs',compute='_compute_values',store = True)
    
    
            
    
    def compute_cost(self, context=None):
        for this in self:
            ## delete table material Labor Marchine
            sql='''
                DELETE FROM mo_direct_cost_collection where cost_collection_id = %s;
                DELETE FROM cost_materials_collection where collection_id = %s;
                DELETE FROM mo_cost_direct where collection_id = %s;
                DELETE FROM costing_premium_line where cost_collection_id = %s
            '''%(this.id,this.id,this.id,this.id)
            self.env.cr.execute(sql)
            # Fin good
            sql = '''
                SELECT mpwpp.product_uom,mpwpp.product_id,sum(mpwpp.product_qty) product_qty 
                FROM  mrp_production_workcenter_line mpwl join 
                    mrp_production_workcenter_product_produce mpwpp on mpwl.id = mpwpp.operation_id
                WHERE production_id = %s
                GROUP BY mpwpp.product_uom,mpwpp.product_id
                HAVING sum(mpwpp.product_qty) > 0
            '''%(this.name.id)
            self.env.cr.execute(sql)
            res = self.env.cr.dictfetchall()
            for res_line in res:
                var ={
                    'cost_collection_id':this.id,
                    'product_id':res_line['product_id'],
                    'product_uom_id':res_line['product_uom'],
                    'produced_qty':res_line['product_qty'],
                    'state': 'draft'
                    }
                self.env['mo.direct.cost.collection'].create(var)
            
            #material
            materials_id = False
            sql ='''
                SELECT distinct sm.product_id
                    FROM mrp_production_consumed_products_move_ids pref join stock_move sm
                        on pref.move_id = sm.id
                    WHERE pref.production_id = %s
            '''%(this.name.id)
            self.env.cr.execute(sql)
            for res_line in self.env.cr.dictfetchall():
                prod_obj = self.env['product.product'].browse(res_line['product_id'])
                var ={
                    'collection_id':this.id,
                    'product_id':prod_obj.id,
                    'product_uom':prod_obj.uom_id.id,
                    'theory_qty':0.0,
                    }
                materials_id = self.env['cost.materials.collection'].create(var)
            
            if materials_id:
                sql ='''
                    SELECT sm.id,sm.product_id,sm.product_uom, product_qty,sm.date
                    FROM mrp_production_consumed_products_move_ids pref join stock_move sm
                        on pref.move_id = sm.id
                    WHERE pref.production_id = %s
                    GROUP BY sm.product_id,product_uom,sm.id
                    order by sm.date desc
                ''' %(this.name.id)
                
                self.env.cr.execute(sql)
                for res_line in self.env.cr.dictfetchall():
                    allocation_id =[]
                    allocation_ids = self.env['stock.move.allocation'].search([('to_move_id','=',res_line['id'])])
                    values = 0.0
                    for allocation in allocation_ids:
                        values = values + allocation.allocated_value
                        allocation_id.append(allocation.id)
                    
                    if not materials_id:
                        raise
                    
                    var ={
                        'allocation_ids':[[6,0,allocation_id]],
                        'date':res_line['date'],
                        'material_id':materials_id.id,
                        'move_id':res_line['id'],
                        'product_id':res_line['product_id'],
                        'product_uom':res_line['product_uom'],
                        'product_qty':res_line['product_qty'],
                        'values': values
                    }
                    self.env['cost.materials.details'].create(var)
                    
                #Kiet: ADD NVL mất mát
                for res_line in self.name.move_loss_ids:
                    allocation_id =[]
                    allocation_ids = self.env['stock.move.allocation'].search([('to_move_id','=',res_line['id'])])
                    values = 0.0
                    for allocation in allocation_ids:
                        values = values + allocation.allocated_value
                        allocation_id.append(allocation.id)
                        
                    var ={
                        'allocation_ids':[[6,0,allocation_id]],
                        'date':res_line.date,
                        'material_id':materials_id.id,
                        'move_id':res_line.id,
                        'product_id':res_line.product_id.id,
                        'product_uom':res_line.product_uom.id,
                        'product_qty':res_line.product_qty,
                        'values': values
                    }
                    self.env['cost.materials.details'].create(var)
                    
            #Các chi phí khác
            nvl_consumed =0.0
            for consum in this.name.move_lines2:
                nvl_consumed += consum.product_qty or 0.0
            
            for consum in this.name.move_loss_ids:
                nvl_consumed += consum.product_qty or 0.0
                
            stack=[]
            for move_ids in this.name.move_lines:
                if move_ids.stack_id.id not in stack:
                    stack.append(move_ids.stack_id.id)
            for stack in self.env['stock.lot'].browse(stack):
                stack.btt_expenses()
                #Kiet: Goi sự kiện gọi Compute Stack
                for expenses in stack.expenses_ids:
                    direct_id = False
                    expenses_ids = self.env['mo.cost.direct'].search([('collection_id','=',this.id),('name','=',expenses.name)])
                    if expenses_ids:
                        expenses_ids.write({'valuesen':expenses.total_values + expenses_ids.valuesen})
                        vals ={
                               'direct_id':expenses_ids.id,
                               'picking_id':expenses.picking_id.id,
                               'product_qty':expenses.product_qty,
                               'cost':expenses.values,
                               'valuesvn':expenses.total_values2rd,
                               'valuesen':expenses.total_values
                               
                               }
                        self.env['mo.cost.direct.line'].create(vals)
                    else:
                        vals ={
                               'product_qty':nvl_consumed,
                               'name':expenses.name or False,
                               'valuesen': expenses.total_values or 0.0,
                               'collection_id':this.id,
                        }
                        direct_id = self.env['mo.cost.direct'].create(vals)
                        vals ={
                               'direct_id':direct_id.id,
                               'picking_id':expenses.picking_id.id,
                               'product_qty':expenses.product_qty,
                               'cost':expenses.values,
                               'valuesvn':expenses.total_values2rd,
                               'valuesen':expenses.total_values
                               
                               }
                        self.env['mo.cost.direct.line'].create(vals)
            
            #Kiet: Tạo bảng tính giá thành
            
            for prem in this.periodical_costing_id.premium_id.prem_ids:
                this.standard_cost = this.periodical_costing_id.premium_id.standard_cost or 0.0
                premium_id = self.env['mrp.bom.premium.line'].search([('flag','=',True)],limit=1)
                produced_qty = 0.0
                sql ='''
                    SELECT sum(produced_qty) produced_qty 
                    FROM mo_direct_cost_collection this where cost_collection_id in (%s)
                    and product_id = %s
                    GROUP BY product_id
                    HAVING sum(produced_qty) >0
                '''%(this.id,prem.product_id.id)
                self.env.cr.execute(sql)
                for y in self.env.cr.dictfetchall():
                    produced_qty = y['produced_qty'] or 0.0
                    
                val ={
                    'cost_collection_id':this.id,
                    'product_id':prem.product_id.id,
                    'product_qty':produced_qty,
                    'premium':prem.premium or 0.0,
                    'price':prem.premium +premium_id.premium
                    }
                self.env['costing.premium.line'].create(val)
            
            a = b = 0.0
            for line in this.premium_ids:
                a += line.product_qty * line.premium
                b += line.product_qty
            
            cp = this.total_cost - a / 1000
            price = b and cp / b or 0.0
            
            for line in this.premium_ids:
                line.price = line.premium/1000 + price
                        
        return True
    
class StockMoveAllocation(models.Model):
    _name = "stock.move.allocation"
    _order = 'in_date,allocated_date'
    
    cost_id = fields.Many2one('cost.materials.collection', 'collection', required=False, ondelete='cascade')
    allocated_qty = fields.Float(string='Basis qty', readonly=False,digits=(12, 0))
    net_qty = fields.Float(string='Net Qty', readonly=True,digits=(12, 0))
    allocated_value = fields.Float(related='from_move_id.price_unit',string='Price ($)', readonly=True)
    
    
    type = fields.Selection([('fifo', 'FIFO'), ('lifo', 'LIFO')], string='Type', default='fifo', readonly=True) 
    #From move  
    from_move_id = fields.Many2one('stock.move.line',string="From Move")
    price_vnd = fields.Float(string='Price (VND)', readonly=True, )
    in_date = fields.Datetime(related='from_move_id.date', string="Incoming Date", readonly=True, store=True)
    from_origin = fields.Char(related='from_move_id.picking_id.origin', string="Origin", readonly=True, store=True)
    picking_id = fields.Many2one(related='from_move_id.picking_id',
                 string="From Picking", store=True)
    to_move_id = fields.Many2one('stock.move',string="To Move")
    #allocated_date = fields.Datetime(related='to_move_id.date', string="Allocated Date", readonly=True, store=True)
    allocated_date = fields.Date(string="Allocated Date", readonly=True)
    warehouse_id = fields.Many2one(related='to_move_id.picking_type_id.warehouse_id', 
                                   string='Warehouse', readonly=True, store=True)
    location_id = fields.Many2one(related='to_move_id.location_id', 
                                   string='Location', readonly=True, store=True)
    
#     from_price_unit = fields.Float(related='from_move_id.price_unit',string="Price Unit")
#     from_product_uom_qty = fields.Float(related='from_move_id.product_uom_qty',string="From Original Qty")
    
    product_id = fields.Many2one(related='from_move_id.product_id', string='Product', readonly=True,store=True)
    uom_id = fields.Many2one('uom.uom', string='UoM', readonly=True)
    allocated_qty = fields.Float(string='Allocated Qty', readonly=True,digits=(12, 0))
    allocated_value = fields.Float(string='Allocated Value', readonly=True)
    
class CostMaterialsCollection(models.Model):
    _name = 'cost.materials.collection'
    _order = 'id desc'
     
    collection_id = fields.Many2one('mrp.production.order.cost.collection', 'MO Cost collection', required=False, ondelete='cascade')
    product_id =fields.Many2one('product.product', 'Product', required=False)
    #categ_id =fields.Many2one('product.category',related='product_id.categ_id',  string= 'Product Categoy', required=False)
    
    theory_qty = fields.Float(string ='Theory Qty',digits=(12, 0))
    theory_value = fields.Float(string ='Theory Value',digits=(12, 0))
    
    material_ids = fields.One2many('cost.materials.details','material_id', 'Materials Details', required=False ,ondelete='cascade')
    state = fields.Selection(selection=[("draft", "Draft"), ("post", "Post")],
                         readonly=True, copy=False,default="draft")          
    
    
    cost_id = fields.Many2one('mrp.periodical.production.costing', 'MO Cost collection', required=False, ondelete='cascade')
    allocation_ids = fields.One2many('stock.move.allocation', 'cost_id', string='FIFO',ondelete='cascade')
    
    @api.depends('material_ids','material_ids.product_qty','material_ids.values')
    def compute_consumed(self):
        for order in self:
            values = init_qty = product_qty = 0.0
            for line in order.material_ids:
                product_qty += line.product_qty
                init_qty += line.init_qty
                values = values + (line.values)
            order.product_qty = product_qty
            order.value = values
            order.init_qty = init_qty
    
    value = fields.Monetary(compute="compute_consumed",string="Consumed Value",store= True,currency_field='company_currency_id')
    product_qty = fields.Float(compute="compute_consumed", string ='Basis Qty',digits=(12, 0),store= True)
    #product_qty = fields.Float(string ='Basis Qty',digits=(12, 0))
    init_qty =fields.Float(compute="compute_consumed", string ='NET Qty',digits=(12, 0),store= True)
    company_currency_id = fields.Many2one('res.currency', related='collection_id.company_currency_id', readonly=True)
    product_uom = fields.Many2one('uom.uom', related='product_id.uom_id', readonly=True)
    
    @api.depends('allocation_ids','allocation_ids.allocated_qty','allocation_ids.from_move_id')
    def compute_fifo_allocation(self):
        for order in self:
            fifo_qty  = 0.0
            price_fifo = 0.0
            for line in order.allocation_ids:
                fifo_qty += line.allocated_qty
                price_fifo += line.allocated_qty * line.allocated_value
                #price_fifo_net += line.net_qty * line.price_vnd
            
#             company = self.env['res.company'].browse(1)
#             second_currency_id = company.second_currency_id
#             price_fifo = second_currency_id.compute(price_fifo, company.currency_id)
#             price_fifo_net = second_currency_id.compute(price_fifo_net, company.currency_id)
            
            order.fifo_qty = fifo_qty
            #order.fifo_net_qty = fifo_net_qty
            order.amount_fifo_qty = price_fifo
            #order.amount_fifo_net_qty = price_fifo_net
            
    fifo_qty = fields.Float(compute="compute_fifo_allocation",string ='FIFO Qty',digits=(12, 0))
    fifo_net_qty = fields.Float(string ='FIFO Request Qty',digits=(12, 0))
    amount_fifo_qty = fields.Monetary(compute="compute_fifo_allocation",string ='FIFO Basis Amount',currency_field='company_currency_id',store= False)
    #fifo_qty = fields.Float(string ='FIFO Qty',digits=(12, 0))
    
    
    def fifo_nvl(self):
        if self.fifo_net_qty !=0:
            self.fifo_allocation()
    
    def fifo_allocation(self):
        line = self
        location_nvp_id = self.env['stock.location'].search([('code','=','NVP - BMT')])
        while(line.fifo_net_qty - line.fifo_qty != 0):
            if line.product_id.default_code != 'FAQ':
#                 sql ='''
#                     DELETE 
#                     FROM stock_move_fifo 
#                     WHERE date(timezone('UTC',create_date::timestamp)) >'%s' 
#                     and product_id= %s
#                 '''%(self.cost_id.name.date_start,line.product_id.id)
#                 self.env.cr.execute(sql)
                
                sql ='''
                    SELECT sm.id, sm.price_unit,sm.price_currency,sm.date
                    FROM stock_move sm
                        join stock_location loc1 on sm.location_id = loc1.id and loc1.id != %s
                        join stock_location loc2 on sm.location_dest_id = loc2.id and loc2.id = %s
                    WHERE 
                        product_id = %s
                        and sm.state ='done'
                        and sm.date > '2016-12-29'
                    order by sm.date
                '''%(location_nvp_id.id,location_nvp_id.id,line.product_id.id)
            else:
                sql ='''
                    SELECT sm.id, sm.price_unit,sm.price_currency,sm.date
                    FROM stock_move sm
                        join stock_location loc1 on sm.location_id = loc1.id and loc1.id != %s
                        join stock_location loc2 on sm.location_dest_id = loc2.id and loc2.id = %s
                    WHERE
                        product_id = %s
                        and picking_id != 84441 -- Dong điêu chỉnh. khong cho chạy FIFO
                        and sm.state ='done'
                        and (sm.price_unit != 0)
                    order by sm.date
                '''%(location_nvp_id.id,location_nvp_id.id,line.product_id.id)
            self.env.cr.execute(sql)
            for incoming in self.env.cr.dictfetchall():
                move = self.env['stock.move'].search([('id','=',incoming['id'])])
                if move and move.fifo:
                    continue
                if line.fifo_net_qty == line.fifo_qty:
                    break
                if move.qty_out_fifo <0:
                    continue
                move = self.env['stock.move'].browse(incoming['id'])
                fifo = line.fifo_net_qty - line.fifo_qty
                unfifo_qty = move.product_qty - (move.fifo_qty  + move.qty_out_fifo)
                #Kiet: Truong hop số lượng stock move lớn hơn lượng cần FIFO
                if fifo - unfifo_qty  >0:
                    qty_fifo = unfifo_qty
                else:
                    qty_fifo = fifo
                if qty_fifo <=0:
                    continue
                val ={
                      'cost_id':line.id,
                      'from_move_id':move.id,
                      'allocated_qty':qty_fifo,
                    }
                allocation_id = self.env['stock.move.allocation'].create(val)
                val ={
                      'fifo_id':move.id,
                      'product_qty':qty_fifo,
                      'fifo_colletion_id':allocation_id.id,
                      'out_qty':qty_fifo
                }
                fifo_id =self.env['stock.move.fifo'].create(val)
                move.refresh()
            return 1
        

class CostMaterialsDetails(models.Model):
    _name = 'cost.materials.details'
    _order = 'id desc'
    
    material_id = fields.Many2one('cost.materials.collection', 'Materials Details', required=False, ondelete='cascade')
    #product_id = fields.Many2one('product.product', 'Product ProdOpenuct', required=False, ondelete='cascade')
    #product_uom = fields.Many2one('uom.uom', 'UoM', required=False, ondelete='cascade')
    #product_qty = fields.Float(string="Consumed Qty",digits=(12, 0))    
    values = fields.Monetary(string="Values Consumed",currency_field='company_currency_id')  
    
    #split_from_moves = fields.One2many('stock.move.allocation', 'to_move_id', string='Split From Moves')
    date = fields.Datetime(string="Date")
    #allocation_ids = fields.Many2many('stock.move.allocation', 'cost_material_rel', 'costing_material_id', 'allocation_id', 'FiFo', required=False)
    company_currency_id = fields.Many2one('res.currency', related='material_id.collection_id.company_currency_id', readonly=True)
    
    move_id = fields.Many2one('stock.move.line', 'Move', required=False)
    #kiet:
    picking_id = fields.Many2one('stock.picking',related='move_id.picking_id',  readonly=True,store= False)
    product_uom = fields.Many2one('uom.uom',related='move_id.product_id.uom_id',string="UoM",  readonly=True,store= True)
    product_id = fields.Many2one('product.product',related='move_id.product_id',string="Product",  readonly=True,store= True)
    init_qty =  fields.Float(related='move_id.init_qty',string="Ned Qty",digits=(12, 0),store= True)  
    product_qty =  fields.Float(related='move_id.qty_done',string="Basis Qty",digits=(12, 0),store= True)
    origin = fields.Many2one(related='move_id.picking_id',string="GIP",store= False) 
    notes = fields.Many2one('mrp.production', string="Mos", readonly=True,store= False)
    #notes = fields.Text(related='move_id.note',string="Mo",store= True) 
#

class CostFinishsDetails(models.Model):
    _name = 'cost.finishs.details'
    _order = 'id desc'
    
    move_id = fields.Many2one('stock.move.line', 'Move', required=False)
    
    fin_id = fields.Many2one('mo.direct.cost.collection', 'Finishs Details', required=False, ondelete='cascade')
    #product_id = fields.Many2one('product.product', 'Product Product', required=False, ondelete='cascade')
    #product_uom = fields.Many2one('uom.uom', 'UoM', required=False, ondelete='cascade')
    #product_qty = fields.Float(string="Basis Qty",digits=(12, 0))   
    #init_qty =  fields.Float(string="Ned Qty",digits=(12, 0))  
    values = fields.Monetary(string="Values Consumed",currency_field='company_currency_id')  
    # move_id = fields.Many2one('stock.move', 'Move', required=False)
    #split_from_moves = fields.One2many('stock.move.allocation', 'to_move_id', string='Split From Moves')
    #date = fields.Datetime(string="Date")
    #allocation_ids = fields.Many2many('stock.move.allocation', 'cost_material_rel', 'costing_material_id', 'allocation_id', 'FiFo', required=False)
    company_currency_id = fields.Many2one('res.currency', related='fin_id.cost_id.company_currency_id', readonly=True)
    picking_id = fields.Many2one('stock.picking',related='move_id.picking_id',  readonly=True)
    product_uom = fields.Many2one('uom.uom',related='move_id.product_id.uom_id',string="UoM",  readonly=True)
    product_id = fields.Many2one('product.product',related='move_id.product_id',string="Product",  readonly=True)
    init_qty =  fields.Float( string="Ned Qty",digits=(12, 0),store= True)  
    product_qty =  fields.Float(string="Basis Qty",digits=(12, 0),store= True)  
    
class MoDirectCostCollection(models.Model):
    _name= 'mo.direct.cost.collection'
    _order = 'id desc'
    
    @api.depends('price_unit','produced_qty')
    def compute_price_subtotal(self):
        for order in self:
            order.price_subtotal = order.price_unit * order.produced_qty
    
    @api.depends('fis_ids','fis_ids.move_id')
    def compute_total_qty(self):
        for order in self:
            init_qty = product_uom =0.0
            for line in order.fis_ids:
                product_uom += line.product_qty
                init_qty += line.init_qty
            order.produced_qty = product_uom
            order.init_qty = init_qty
            
    cost_collection_id = fields.Many2one('mrp.production.order.cost.collection', 'MO Cost collection', required=False, ondelete='cascade')
    product_id = fields.Many2one('product.product', 'Product', required=True)
    #product_uom_id = fields.Many2one('uom.uom', 'UoM', required=True)
    produced_qty = fields.Float('Basis Qty',compute="compute_total_qty", digits=(12, 0), readonly=True)
    init_qty = fields.Float('Net Qty',compute="compute_total_qty", digits=(12, 0), readonly=True)
    price_unit = fields.Monetary('Unit Price', currency_field='company_currency_id')
    price_subtotal = fields.Monetary('Price Subtotal',compute="compute_price_subtotal",currency_field='company_currency_id',store= True)
    company_currency_id = fields.Many2one('res.currency', related='cost_collection_id.company_currency_id', readonly=True)
    
    #Moi them
    cost_id = fields.Many2one('mrp.periodical.production.costing', 'MO Cost collection', required=False, ondelete='cascade')
    fis_ids = fields.One2many('cost.finishs.details', 'fin_id', string='GRP')
    product_uom_id = fields.Many2one('uom.uom', related='product_id.uom_id',string="UoM", readonly=True)

class MoCostDirect(models.Model):
    _name= 'mo.cost.direct'
    _order = 'id desc'
    
    @api.depends('valuesen')
    def _compute_values(self):
        for this in self:
            total_qty = 0.0
            for move in this.collection_id.name.move_lines:
                total_qty += move.product_qty or 0.0
            this.total_consume = total_qty and this.product_qty * this.valuesen /total_qty or 0.0
        
    name = fields.Char(string="Name")
    valuesen = fields.Monetary(string="Total Values",currency_field='company_currency_id')
    product_qty = fields.Float(string="Qty Consumed",digits=(12, 0))
    collection_id = fields.Many2one('mrp.production.order.cost.collection', 'MO Cost collection', required=False, ondelete='cascade')
    total_consume = fields.Monetary(string='Value Consume',compute='_compute_values', store = True,currency_field='company_currency_id')
    company_currency_id = fields.Many2one('res.currency', related='collection_id.company_currency_id', readonly=True)
    second_currency_id  = fields.Many2one(related='company_id.second_currency_id',  string="Currency",store= False)
    company_id  = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)
    direct_line = fields.One2many('mo.cost.direct.line','direct_id', 'Direct Details', required=False)
    
    cost_id = fields.Many2one('mrp.periodical.production.costing', 'MO Cost collection', required=False, ondelete='cascade')
    


class MoCostDirectLine(models.Model):
    _name= 'mo.cost.direct.line'
    _order = 'id desc'
    
    direct_id = fields.Many2one('mo.cost.direct', 'Direct Cost Details', required=False, ondelete='cascade')
    picking_id = fields.Many2one('stock.picking', 'GRN', required=False, ondelete='cascade')
    product_qty = fields.Float(string="GRN Qty",digits=(12, 0))    
    cost = fields.Monetary(string="Cost",currency_field='second_currency_id')    
    valuesvn = fields.Monetary(string="Total Values",currency_field='second_currency_id')    
    valuesen = fields.Monetary(string="Total Values",currency_field='com_currency_id')   
    company_id  = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)
    second_currency_id = fields.Many2one('res.currency',related='company_id.second_currency_id', string="2rd Currency", readonly=True)
    com_currency_id = fields.Many2one('res.currency', related='company_id.currency_id',string="Currency", readonly=True)
    
    
    
    
