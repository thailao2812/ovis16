# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
import time


class wizard_purchase_contract(models.TransientModel):
    _name = "wizard.purchase.contract"
    _description = "Wizard Purchase Contract"

    purchase_contract_id = fields.Many2one('purchase.contract', required=False, readonly=True)
    date_order = fields.Date(string='Date Order')
    contract_line_ids = fields.One2many('wizard.purchase.contract.line', 'contract_id', 'Product Line', required=False)
    name = fields.Char('Name', size=128)
    price_unit = fields.Float(string='Price Unit', required=False)

    def button_convert(self):
        npe_nvp_relation = self.env['npe.nvp.relation']
        
        for line in self.contract_line_ids:
            if line.qty_received < line.product_qty+ line.total_qty_fixed:
                raise UserError('Cannot create a NVP if Qty Received > Fixed + Qty Fix')
        origin =''
        for line in self._context.get('active_ids'):
            origin += self.env['purchase.contract'].browse(line).name
            origin +=';'
            
        #Ràng buộc diều kiện lãi
        for line in self._context.get('active_ids'):
            for npe in self.env['purchase.contract'].browse(line):
                # if not npe.request_payment_ids:
                #     raise UserError('Please input request payment for NPE before Convert to NVP')
                # else:
                for pay in npe.request_payment_ids:
                    if not pay.rate_ids:
                        raise UserError('You need to input interest before convert to NVP')
                    for rate in pay.rate_ids:
                        if not rate.date or not rate.date_end:
                            raise UserError('You need to input interest and date from - date to before convert to NVP')
            
        active_id = self._context.get('active_id')
        company = self.env.user.company_id.id
        warehouse_id = self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1)
        npe = self.env['purchase.contract'].browse(active_id)
        npe_line = npe.contract_line[0]
        new_id = npe.copy({'warehouse_id':warehouse_id.id, 'name': 'New','nvp_ids':[], 'cert_type': 'normal',
            'contract_line':[], 'type':'purchase', 'npe_contract_id':active_id,'origin':origin})
        # ràng buộc dữ liệu
         # Kiet + 7 date cập nhật deadline date
        new_id.license_id = npe.license_id.id if npe.license_id else False
        new_id.onchange_date_order()
        
        for line in self.contract_line_ids:
            vals ={
                   'npe_contract_id':line.purchase_contract_id.id,
                   'contract_id':new_id.id,
                   'product_qty':line.product_qty or 0.0,
                   'type':'fixed',
                   }
            npe_nvp_relation.create(vals)
                    
        sql ='''
            select product_id,sum(product_qty) product_qty 
            FROM wizard_purchase_contract_line 
            WHERE contract_id = %s
            Group By product_id
        '''%(self.id)
        self.env.cr.execute(sql)
        for r in self.env.cr.dictfetchall():
            npe_line.copy({'product_qty':r['product_qty'],'price_unit':self.price_unit ,'contract_id':new_id.id})
            new_id.qty_received += r['product_qty']
            
        result = False 
        if new_id:                 
        
            action = self.env.ref('sd_purchase_contract.action_purchase_contract')
            result = action.read()[0]
            res = self.env.ref('sd_purchase_contract.view_purchase_contract_form', False)
            result['context'] = {}
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = new_id.ids[0] or False
        return result
    
    
    def button_convert_ptbf(self):
        npe_nvp_relation = self.env['npe.nvp.relation']
        
        for line in self.contract_line_ids:
            if line.qty_received < line.product_qty+ line.total_qty_fixed:
                raise UserError('Cannot create a NVP if Qty Received > Fixed + Qty Fix')
        origin =''
        for line in self._context.get('active_ids'):
            origin += self.env['purchase.contract'].browse(line).name
            origin +=';'
            
        active_id = self._context.get('active_id')
        company = self.env.user.company_id.id
        warehouse_id = self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1)
        npe = self.env['purchase.contract'].browse(active_id)
        npe_line = npe.contract_line[0]
        new_id = npe.copy({'warehouse_id':warehouse_id.id, 'name': 'New','nvp_ids':[],
            'contract_line':[], 'type':'ptbf', 'npe_contract_id':active_id,'origin':origin})
        
        # Kiet + 7 date cập nhật deadline date
        new_id.onchange_date_order()
        # ràng buộc dữ liệu
        
        for line in self.contract_line_ids:
            vals ={
                   'npe_contract_id':line.purchase_contract_id.id,
                   'contract_id':new_id.id,
                   'product_qty':line.product_qty or 0.0,
                   'type':'fixed'
                   }
            npe_nvp_relation.create(vals)
                    
        sql ='''
            select product_id,sum(product_qty) product_qty 
            FROM wizard_purchase_contract_line 
            WHERE contract_id = %s
            Group By product_id
        '''%(self.id)
        self.env.cr.execute(sql)
        for r in self.env.cr.dictfetchall():
            npe_line.copy({'product_qty':r['product_qty'],'price_unit':self.price_unit ,'contract_id':new_id.id})
            new_id.qty_received += r['product_qty']
        
        result = False
        if new_id:     
            action = self.env.ref('sd_purchase_contract.action_ptbf_contract')
            result = action.read()[0]
            res = self.env.ref('sd_purchase_contract.view_ptbf_contract_form', False)
            result['context'] = {}
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = new_id.ids[0] or False
                        
        return result

    @api.model
    def default_get(self, fields):
        res = {}
        val = []
        sql ='''
            SELECT count(distinct partner_id) count_partner,
                    count(distinct delivery_place_id) count_place
            FROM purchase_contract
            WHERE id in (%s)
        '''%(','.join(map(str, self._context.get('active_ids'))))
        self.env.cr.execute(sql)
        for r in self.env.cr.dictfetchall():
            if r['count_partner']>1:
                raise UserError('You must select NPE with the same Vendor.')
            if r['count_place']>1:
                raise UserError('You must select NPE with the same Delivery Place.')
        
        
        for active_id in self._context.get('active_ids'):
            if self._context.get('active_model',False) ==  'ptbf.fixprice':
                contract_obj = self.env['purchase.contract'].browse(self._context.get('default_purchase_contract_id'))
            else:
                contract_obj = self.env['purchase.contract'].browse(active_id)
                
            for line in contract_obj.contract_line:
                product_remain_qty =0.0
                for relation in  self.env['npe.nvp.relation'].search([('npe_contract_id','=',line.contract_id.id)]):
                    product_remain_qty += relation.product_qty or 0.0
                
                val.append((0, 0, {
                     'product_id':line.product_id.id,
                     'product_uom':line.product_uom.id,
                     'product_qty':line.contract_id.qty_received - line.contract_id.total_qty_fixed,
                     'purchase_contract_id':line.contract_id.id,
                     'qty_received':line.contract_id.qty_received or 0.0,
                     'total_qty_fixed': line.contract_id.total_qty_fixed or 0.0,
                     'qty_unreceived': line.contract_id.qty_received - product_remain_qty or 0.0,
                     'product_remain_qty':line.product_qty - product_remain_qty
                     }))
            res.update({'contract_line_ids':val})
        return res
    
class wizard_purchase_contract_line(models.TransientModel):
    _name = "wizard.purchase.contract.line"
    _description = "Wizard Purchase Contract Line"
    
    
    @api.depends('product_id')  
    def _product_remain_qty(self):
        for order in self:
            product_remain_qty = 0.0
            if order.purchase_contract_id:
                for relation in  self.env['npe.nvp.relation'].search([('npe_contract_id','=',order.purchase_contract_id.id)]):
                    product_remain_qty += relation.product_qty or 0.0
                
                order.product_remain_qty = order.product_qty - product_remain_qty
            
    product_id = fields.Many2one('product.product', string='Product', required=True)
    product_uom = fields.Many2one('uom.uom', string='UoM', required=True)
    product_qty = fields.Float(string='Contract Qty', digits=(16, 0), required=True, default=1.0)
    price_unit = fields.Float(string='Price Unit', required=False,digits=(16, 0))
    contract_id = fields.Many2one('wizard.purchase.contract', 'Purchase Contract', required=False)
    purchase_contract_id = fields.Many2one('purchase.contract', 'Purchase Contract', required=False)
    product_remain_qty = fields.Float(compute='_product_remain_qty', string='Product Remain', default=0,  store= True, digits=(16, 0))
    
    qty_received = fields.Float(string ='Received',digits=(12, 0))
    total_qty_fixed = fields.Float(string ='Fixed',digits=(12, 0))
    qty_unreceived = fields.Float(string ='Unfixed',digits=(12, 0))
    
    
