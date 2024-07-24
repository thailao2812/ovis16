# -*- coding: utf-8 -*-

import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
import time

    
    
class wizard_ptbf_contract(models.TransientModel):
    _name = "wizard.ptbf.contract"
    
    purchase_contract_id = fields.Many2one('purchase.contract', required=False, readonly=True)
    date_order = fields.Date(string='Date Fixed')
    contract_line_ids = fields.One2many('wizard.ptbf.contract.line', 'contract_id', 'Product Line', required=False)
    name = fields.Char('Name', size=128)
    rate = fields.Float(string='Rate', required=False, default=1)
    
    
    @api.model
    def default_get(self, fields):
        res = {}
        val = []
              
        for line in self.env['ptbf.fixprice'].browse(self._context.get('active_ids')):
            val.append((0, 0, {
                 'product_id':line.product_id.id,
                 'product_uom':line.product_id.uom_id.id,
                 'product_qty':line.quantity_unfixed,
                 'purchase_contract_id':line.contract_id.id,
                 'price_fix':line.final_price,
                 }))
        res.update({'contract_line_ids':val})
        return res
    
    def button_convert(self):
        npe_nvp_relation = self.env['npe.nvp.relation']
        history_rate = self.env['history.rate']
        
        origin =''
        contract_id = False
        for line in self.env['ptbf.fixprice'].browse(self._context.get('active_ids')) :
            origin += line.contract_id.name
            origin +=';'
            contract_id = line.contract_id
            
        company = self.env.user.company_id.id
        warehouse_id = contract_id.warehouse_id
        ptbf = contract_id
#         npe_line = ptbf.contract_line[0]
#         new_id = ptbf.copy({'warehouse_id':warehouse_id.id, 'name': 'New','nvp_ids':[],
#             'contract_line':[], 'type':'purchase', 'npe_contract_id':ptbf.id,'origin':origin})
        # ràng buộc dữ liệu
        
        for line in self.contract_line_ids:
            vals ={
                   'date_receive':self.date_order,
                   'product_id':line.product_id.id,
                   'rate':self.rate,
                   'history_id': self._context.get('active_id'),
                   'ptbf_id':line.purchase_contract_id.id,
                   'qty_price':line.product_qty or 0.0,
                   'final_price_en':line.price_fix,
                   'final_price_vn':line.price_amount_vn or round((line.price_fix * line.contract_id.rate) /1000,0),
                   # 'final_price':line.price_amount_vn,
                   'total_amount_en':line.total_amount,
                   'total_amount_vn':line.total_amount_vn
                   }
                   # 'final_price_vn':round((line.price_fix * line.contract_id.rate) /1000,0),
            new_id = history_rate.create(vals)
        self.createPicking(new_id)
                    
        return True
    
    # @api.depends('contract_line_ids','contract_line_ids.price_fix','contract_line_ids.contract_id.rate')
    def _get_final_price_vn(self, final_price_vn):
        for i in self.contract_line_ids:
            final_price_vn = 0
            if i.contract_id.rate:
                final_price_vn = round((i.price_fix * i.contract_id.rate) /1000,0)
            else:
                final_price_vn = i.price_amount_vn
            return final_price_vn

        
    
    def createPicking(self, new_id):
        contract_id = False
        for line in self.env['ptbf.fixprice'].browse(self._context.get('active_ids')):
            contract_id = line.contract_id
        company = self.env.user.company_id.id

        picking_type = self.env['stock.picking.type'].sudo().search([('name', '=', 'NPE -> NVP')])
        purchase_contract_id = contract_id

        var = {
            'warehouse_id': picking_type.warehouse_id.id,
            'picking_type_id': picking_type.id,
            'partner_id': purchase_contract_id.partner_id.id,
            'date': self.date_order,
            'date_done': self.date_order,
            'origin': purchase_contract_id.name,
            'location_dest_id': picking_type.default_location_dest_id.id,
            'location_id': picking_type.default_location_src_id.id,
            'purchase_contract_id': purchase_contract_id.id,
            'rate_ptbf': self.rate
        }
        picking = self.env['stock.picking'].sudo().create(var)
        new_id.grn_id = picking.id

        for line in self.contract_line_ids:
            moves = self._create_stock_moves(line, picking, picking_type)
            
        picking.button_sd_validate()
        
        
        # self.get_entries_picking_nvp(picking, self.rate)
    
    def _get_accounting_faq_data(self,line):
        product_obj = self.env['product.template']
        accounts = product_obj.browse(line.product_id.product_tmpl_id.id).get_product_accounts()
        
        acc_src = accounts['stock_input'].id
        acc_dest = accounts.get('stock_valuation', False)
        
        journal_id = accounts['stock_journal'].id
        return journal_id, acc_dest.id, acc_src
    
    def _prepare_account_move_faq_line(self,line, qty,amount_usd, debit_account_id, credit_account_id,rate):
        debit = credit = amount_usd
        partner_id = (line.picking_id.partner_id and self.pool.get('res.partner')._find_accounting_partner(line.picking_id.partner_id).id) or False
        #name =''
#         if line.picking_id:
#             name = line.picking_id.origin + ' - ' +line.product_id.default_code
#         else:
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
            'account_id': debit_account_id,
            'currency_id': line.company_id.second_currency_id.id,
            'rate_type':'transaction_rate',
            'currency_ex_rate':rate,
            'amount_currency':debit * rate
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
            'account_id': credit_account_id,
            'currency_id': line.company_id.second_currency_id.id,
            'rate_type':'transaction_rate',
            'currency_ex_rate': rate,
            'amount_currency': (-1) * credit * rate
        }
        return [(0, 0, debit_line_vals), (0, 0, credit_line_vals)]
    
    def get_entries_picking_nvp(self,pick,rate):
        move_obj = self.env['account.move']
        move_lines =[]
        
        for move_line_ids in pick.move_lines:
            journal_id, acc_src, acc_dest  = self._get_accounting_faq_data(move_line_ids)
            move_lines = self._prepare_account_move_faq_line(move_line_ids, move_line_ids.product_qty ,move_line_ids.price_unit * move_line_ids.product_uom_qty , acc_src,acc_dest,rate)
            if move_lines:
                if move_line_ids.entries_id:
                    return False
                ref = move_line_ids.picking_id.name
                date = move_line_ids.date
                new_move_id = move_obj.sudo().create({'journal_id': journal_id,
                                      'account_analytic_id':pick.warehouse_id and pick.warehouse_id.account_analytic_id.id,
                                      'line_ids': move_lines,
                                      'date': date,
                                      'ref': ref,
                                      'warehouse_id':pick.warehouse_id and pick.warehouse_id.id or False,
                                      'narration':False})
                new_move_id.post()
                move_line_ids.entries_id = new_move_id.id
                return  True
        else:
            return False
    
    def _create_stock_moves(self, line, picking, picking_type):
        moves = self.env['stock.move.line']
        price_unit = line.price_fix/1000
        vals = {
            'warehouse_id':picking_type.warehouse_id.id,
            'picking_id': picking.id,
            #'name': line.purchase_contract_id.name or '',
            'product_id': line.product_id.id,
            'product_uom_id': line.product_id.uom_id.id,
            'init_qty':line.product_qty,
            'qty_done': line.product_qty or 0.0,
            'price_unit': price_unit,
            # 'tax_id': [(6, 0, [x.id for x in i.tax_id])],
            'picking_type_id': picking_type.id,
            'location_id': picking_type.default_location_src_id.id,
            'location_dest_id': picking_type.default_location_dest_id.id,
            'date': line.contract_id.date_order,
            # 'exchange_rate':this.purchase_contract_id.exchange_rate or 1,
            'currency_id':line.purchase_contract_id.currency_id.id or False,
            # 'type': picking_type.code,
            'state':'draft',
            # 'scrapped': False,
        }
        move_id = moves.sudo().create(vals)
        return move_id


class wizard_ptbf_contract_line(models.TransientModel):
    _name = "wizard.ptbf.contract.line"
    
    qty_received = fields.Float(string ='Received',digits=(12, 0))
    total_qty_fixed = fields.Float(string ='Fixed',digits=(12, 0))
    qty_unreceived = fields.Float(string ='Unfixed',digits=(12, 0))
    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)], change_default=True, required=True)
    product_uom = fields.Many2one('uom.uom', string='UoM', required=True)
    product_qty = fields.Float(string='Contract Qty', digits=(16, 0), required=True, default=1.0)
    price_unit = fields.Float(string='Price Unit', required=False,digits=(16, 0))
    contract_id = fields.Many2one('wizard.ptbf.contract', 'Purchase Contract', required=False)
    purchase_contract_id = fields.Many2one('purchase.contract', 'Purchase Contract', required=False)
    price_fix = fields.Float(string="Final Price")
    packing_id = fields.Many2one('ned.packing', string='Packing')
    
    @api.depends('product_qty','price_fix','contract_id.rate','contract_id')
    def _compute_amount(self):
        for line in self:
            line.total_amount = line.product_qty/1000 * line.price_fix
#             line.total_amount_vn = line.product_qty/1000 * line.price_fix * line.contract_id.rate
            line.price_amount_vn = round((line.price_fix * line.contract_id.rate) /1000,0)
            line.total_amount_vn = line.price_amount_vn * line.product_qty
            
    total_amount = fields.Float(string="Total Amount",compute='_compute_amount',store= True)
    price_amount_vn = fields.Float( string='Price vn', default=0,  digits=(16, 0),)
    total_amount_vn = fields.Float( string='Amount vn', default=0,  digits=(16, 0))
    
    
    
    
    
    
