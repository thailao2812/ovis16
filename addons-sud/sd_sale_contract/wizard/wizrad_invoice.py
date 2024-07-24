# -*- coding: utf-8 -*-

import time
from datetime import datetime
# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
from pytz import timezone


class wizrad_invoice(models.TransientModel):
    _name = "wizard.invoice"
    
    name = fields.Char(string='Invoice Number')
    date = fields.Date(string='Date', default=fields.Datetime.now, required=False)
    journal_id = fields.Many2one("account.journal", 'Journal', required=True)
    currency_id = fields.Many2one("res.currency", string="Currency", required=True)
    wizard_ids = fields.One2many('wizard.invoice.line', 'wizard_id', 'Wizard Lines')
    
    @api.model
    def default_get(self, fields):
        res = {}    
        vars = []
        active_id = self._context.get('active_id')
        if active_id:
            
            si = self.env['sale.contract'].browse(active_id)
            
            nvs =si.name[4:len(si.name)]
            now = datetime.now()
            current_year = str(now.year)
            current_year = current_year[2:4]
    
            name ='INV-'+ str(current_year) + nvs
            
            #'contract_id': active_id,
            journal_ids = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
            res = { 'date': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT) or False,
                   'currency_id': si.currency_id.id or False,'name':name, 'journal_id': journal_ids.id}
            
            for line in si.contract_line:
                vars.append((0, 0, {'product_id':line.product_id.id,'product_qty': line.product_qty or 0.0, 'product_uom':line.product_uom.id,
                                'price_unit': line.price_unit or 0.0, 
                                'sale_contract_line_id':line.id}))
                res.update({'wizard_ids':vars})
        return res
    
    def _get_taxes_invoice(self, move_line, type):
        taxes = move_line.product_id.taxes_id
        if move_line.picking_id and move_line.picking_id.partner_id and move_line.picking_id.partner_id.id:
            position = self.env['account.fiscal.position'].browse(move_line.picking_id.partner_id.property_account_position_id.id)
            return position.map_tax(taxes)
        else:
            return map(lambda x: x.id, taxes)
    
    def _get_account_analytic_invoice(self, picking, move_line):
        return False
    
    def _prepare_invoice_line(self,  move_line, invoice_id, invoice_vals):
        name = move_line.product_id.name or ''
        origin = move_line.product_id.name or ''
        
        account_id = False
        if self.journal_id.default_account_id:
            account_id = self.journal_id.default_account_id.id or False
        
        if not account_id:
            account_id = move_line.product_id.property_account_income_id.id or False
        if not account_id:
            account_id = move_line.product_id.categ_id.property_account_income_categ_id.id or False
                    
        if invoice_vals['fiscal_position_id']:
            fp_obj = self.env['account.fiscal.position']
            fiscal_position = fp_obj.browse(invoice_vals['fiscal_position_id'])
            account_id = fiscal_position.map_account(account_id)
      
        uos_id = move_line.product_id and move_line.product_id.uom_id.id or False
        if not uos_id and invoice_vals['type'] == 'out_invoice':
            uos_id = move_line.product_uom.id

        return {'name': name, 
                 #'origin': origin,
                'move_id': invoice_id.id, 'product_id': move_line.product_id.id,
                'account_id': account_id, 'price_unit': move_line.price_unit or 0.0, 
                'quantity': move_line.product_qty,
                'product_uom_id':move_line.product_uom and move_line.product_uom.id or False
            #'invoice_line_tax_ids': [(6, 0, self._get_taxes_invoice(move_line, invoice_vals['type']))]
            }
          
    def create_invoice(self):
        active_id = self._context.get('active_id')
        invoice_pool = self.env['account.move']
        invoice_line_pool = self.env['account.move.line']
        si = self.env['sale.contract'].browse(active_id)
                    
        partner_id = si.partner_id or False
            
        account_id = partner_id.property_account_receivable_id.id or False
        payment_term = partner_id.property_payment_term_id.id or False
            
#         nvs =si.name[4:len(si.name)]
#         now = datetime.now()
#         current_year = now.year
# 
#         name ='INV-'+ str(current_year) +'.'+ nvs
        
        invoice_vals = {'name': 'Draft',
                        'origin': si.name, 
                        #'supplier_inv_date': False, 
                        'trans_type':self.journal_id.trans_type and self.journal_id.trans_type or 'export',
                        'partner_id': partner_id.id, 
                        'payment_reference': self.name,
                        'move_type': 'out_invoice', 
                        #'account_id': account_id, 
                        'invoice_date': self.date or False, 
                        'currency_id': self.currency_id.id or False,
                        'narration': '', 
                        'company_id': 1, 
                        'user_id': self.env.uid, 
                        'journal_id': self.journal_id.id or False,
                        'invoice_payment_term_id': payment_term, 
                        'fiscal_position_id': partner_id.property_account_position_id.id or False, 
                        'sale_contract_id': si.id or False}
        
        invoice_id = invoice_pool.create(invoice_vals)
        for line in self.wizard_ids:
            vals = self._prepare_invoice_line( line, invoice_id, invoice_vals)
            invoice_line_pool.create(vals)
        
                    
        if invoice_id:                 
            action = self.env.ref('account.action_move_out_invoice_type')
            result = action.read()[0]
            res = self.env.ref('account.view_move_form', False)
            result['context'] = {}
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = invoice_id.id or False
            return result
            
                
class wizard_invoice_line(models.TransientModel):
    _name = "wizard.invoice.line"
    
    @api.onchange('product_uom', 'product_qty')
    def onchange_uom(self):
        for i in self:
            product_uom = 0
            if i.sale_contract_line_id.product_uom.id != i.product_uom.id:
                i.product_qty = i.sale_contract_line_id.product_qty /1000
            else:
                i.product_qty = i.sale_contract_line_id.product_qty
        
                
    
    wizard_id = fields.Many2one('wizard.invoice', string='Wizard invoice', ondelete='cascade')
    do_id = fields.Many2one('delivery.order', string='Delivey Order', readonly=True)
    picking_id = fields.Many2one('stock.picking', string='Picking', readonly=True)
    check_picking = fields.Boolean('Check', default=True)        
    
    product_id = fields.Many2one('product.product', string='Product', ondelete='cascade',required=True,)
    product_qty = fields.Float(string='product Qty',digits=(12, 3) )
    price_unit= fields.Float(string='Price Unit', digits=(12, 3) )
    product_uom = fields.Many2one('uom.uom',string="Uom")
    sale_contract_line_id = fields.Many2one('sale.contract.line',string="Contract Line")
    
