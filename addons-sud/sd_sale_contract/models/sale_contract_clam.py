# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

    
class SaleContractClam(models.Model):
    _name= 'sale.contract.clam'
    _description = 'Sale Contract Clam'
    _order = 'id desc'
    
    contract_id= fields.Many2one('sale.contract', string='Clam', required=True,ondelete='cascade')
    name = fields.Char(string="Reason")
    product_qty = fields.Float(string="Product Qty")
    price_unit = fields.Float(string="Price Unit")
    move_id = fields.Many2one('account.move', string='Move', required=False,ondelete='cascade',readonly = True)
    state = fields.Selection([
        ('draft','Draft'),
        ('validate','Validated'),
        ],'Status', readonly=True,default='draft')
    
    @api.depends('price_unit','product_qty','state')
    def compute_price(self):
        for order in self:
            if order.product_qty and order.price_unit:
                order.amount = order.product_qty * order.price_unit
            else:
                order.amount = 0.0
            
    amount = fields.Float(string="Amount",compute="compute_price")
    
    def _prepare_account_move_line(self, credit_account_id, debit_account_id):
        debit = credit = self.price_unit * self.product_qty or 0.0
        
        debit_line_vals = {
            'name': self.contract_id.name +'-' + self.name,
            'product_id': False,
            'quantity': self.product_qty,
            'ref': self.name,
            'partner_id': self.contract_id.partner_id.id,
            'debit': debit or 0,
            'credit': 0,
            'account_id': debit_account_id,
        }
        credit_line_vals = {
            'name': self.contract_id.name +'-' + self.name,
            'product_id': False,
            'quantity': self.product_qty,
            'ref': self.name,
            'partner_id': self.contract_id.partner_id.id,
            'credit': debit,
            'debit': 0,
            'account_id': credit_account_id,
        }
        return [(0, 0, debit_line_vals), (0, 0, credit_line_vals)]
    
    def btt_cancel(self):
        if self.move_id:
            self.move_id.button_cancel()
            self.move_id.unlink()
            self.state = 'draft'
        
    def btt_validate(self):
        if not self.move_id:
            move_obj = self.env['account.move']
            journal_id = self.env['account.journal'].search([('type','=','sale'),('code','=','BHXK')])
            
            if self.contract_id.type =='export':
                debit_account_id = self.contract_id.product_id.categ_id.property_account_cogs_export.id
            else:
                debit_account_id = self.contract_id.product_id.categ_id.property_account_cogs_local.id
            
            credit_account_id = self.contract_id.product_id.categ_id.property_stock_account_output_categ_id.id
            
            move_lines = self._prepare_account_move_line(credit_account_id, debit_account_id)
            date = datetime.now().strftime(DEFAULT_PDF_DATETIME_FORMAT)
            new_move_id = move_obj.create({'journal_id': journal_id.id,
                                      'line_ids': move_lines,
                                      'date': date,
                                      'ref': self.contract_id.name +'-' + self.name,
                                      'narration':self.contract_id.name +'-' + self.name})
            
            self.move_id = new_move_id.id
            self.state = 'validate'
            new_move_id.post()
            return True