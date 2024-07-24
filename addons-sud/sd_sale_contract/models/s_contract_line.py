# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
    
class SContractLine(models.Model):
    _name = "s.contract.line"
    
    
    original_diff = fields.Float(string='Original Diff')
    no_of_teus  = fields.Float(string='No. of teus')
    
    def onchange_bags_qty(self):
        if self.product_qty:
            self.number_of_bags = self.product_qty /60
    
    def _compute_tax_id(self):
        for line in self:
            fpos = line.contract_id.partner_id.property_account_position_id
            if fpos:
                if self.env.uid == SUPERUSER_ID and line.contract_id.company_id:
                    taxes = fpos.map_tax(line.product_id.taxes_id).filtered(lambda r: r.company_id == line.contract_id.company_id)
                else:
                    taxes = fpos.map_tax(line.product_id.taxes_id)
                line.tax_id = taxes
            else:
                line.tax_id = line.product_id.taxes_id if line.product_id.taxes_id else False
                
    # @api.depends('product_qty', 'price_unit', 'tax_id')
    # def _compute_amount(self):
    #     for line in self:
    #         price = line.price_unit
    #         taxes = line.tax_id.compute_all(price, line.contract_id.currency_id, line.product_qty, product=line.product_id, partner=line.contract_id.partner_id)
    #         line.update({
    #             'price_tax': taxes['total_included'] - taxes['total_excluded'],
    #             'price_total': taxes['total_included'],
    #             'price_subtotal': taxes['total_excluded'],
    #         })
    
    @api.depends('product_qty', 'price_unit', 'tax_id','market_price', 'p_contract_diff')
    def _compute_amount(self):
        for line in self:
            if line.type != 'p_contract':
                price = line.price_unit
                taxes = line.tax_id.compute_all(price, line.contract_id.currency_id, line.product_qty, product=line.product_id, partner=line.contract_id.partner_id)
                
                line.price_tax = 0
                line.price_total = 0
                line.price_subtotal = 0
                line.final_price = 0.0
                # line.update({
                #     'price_tax': taxes['total_included'] - taxes['total_excluded'],
                #     'price_total': taxes['total_included'],
                #     'price_subtotal': taxes['total_excluded'],
                #     'final_price':0.0
                # })
            else:
                line.price_tax = 0.0
                line.price_total = (line.market_price + line.p_contract_diff)*line.product_qty
                line.price_subtotal = (line.market_price + line.p_contract_diff)*line.product_qty
                line.final_price = line.market_price + line.p_contract_diff
                
                
                
                # line.update({
                # 'final_price': line.market_price + line.p_contract_diff,
                # 'price_subtotal' : (line.market_price + line.p_contract_diff)*line.product_qty,
                # 'price_total': (line.market_price + line.p_contract_diff)*line.product_qty,
                # })
    
    
    
    
    name = fields.Text(string='Description', required=True)
    contract_id = fields.Many2one('s.contract', string='Contract Reference', ondelete='cascade', index=True, copy=False)
    sequence = fields.Integer(string='Sequence', default=10)
    company_id = fields.Many2one(related='contract_id.company_id', string='Company', store=True, readonly=True)
    partner_id = fields.Many2one(related='contract_id.partner_id', store=True, string='Customer')
    
    state = fields.Selection(selection=[('draft', 'New'), ('approved', 'Approved'),
                                        ('done', 'Done'), ('cancel', 'Cancelled')],
          related='contract_id.state', string='Status', readonly=True, copy=False, store=True, default='draft')
    
    currency_id = fields.Many2one(related='contract_id.currency_id', store=True, string='Currency', readonly=True)
    
    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)], change_default=True, required=True)
    product_qty = fields.Float(string='Qty', required=True, default=1.0)
    product_uom = fields.Many2one('uom.uom', string='Uom', required=True)
    price_unit = fields.Float('Unit Price', required=True, default=0.0)
    tax_id = fields.Many2many('account.tax', string='Taxes',)
    
    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', readonly=True, store=True)
    price_tax = fields.Monetary(compute='_compute_amount', string='Taxes', readonly=True, store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total', readonly=True, store=True)

    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return {'domain': {'product_uom': []}}

        vals = {}
        domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        if not (self.product_uom and (self.product_id.uom_id.category_id.id == self.product_uom.category_id.id)):
            vals['product_uom'] = self.product_id.uom_id

        product = self.product_id.with_context(
            lang=self.contract_id.partner_id.lang,
            partner=self.contract_id.partner_id.id,
            quantity=self.product_qty,
            uom=self.product_uom.id
        )

        name = product.name_get()[0][1]
        if product.description_sale:
            name += '\n' + product.description_sale
        vals['name'] = name

        self._compute_tax_id()

        #Kiet ko hieu
        # if self.contract_id.partner_id:
        #     vals['price_unit'] = self.env['account.tax']._fix_tax_included_price(product.price, product.taxes_id, self.tax_id)
        self.update(vals)
        return {'domain': domain}
    
    ##################################################################################################################################################
    
    @api.depends('p_contract_id','contract_id')
    def _compute_state(self):
        for this in self:
            if this.p_contract_id:
                this.type = this.p_contract_id.type
            elif this.contract_id:
                this.type = this.contract_id.type

    def compute_remaning_qty(self):
        remaining_qty = 0.0
        for this in self:
            if this.type == 'p_contract':
                nvs_ids = self.env['sale.contract'].search([('contract_p_id','=', this.p_contract_id.id),('state','!=','cancel')])
                qty_allocated = sum([x.product_qty for x in [y.contract_line for y in nvs_ids]])
                remaining_qty = this.product_qty - (qty_allocated/this.product_uom.factor_inv)
            this.update({
                'remainning_qty': remaining_qty
            })
            
            
            
    packing_id = fields.Many2one('ned.packing', string='Packing')
    certificate_id = fields.Many2one('ned.certificate', string='Certificate')
    license_id = fields.Many2one('ned.certificate.license', string='License')


    type = fields.Selection([('p_contract','P Contract'),('local', 'Local'), ('export', 'Export')],string="Type", compute='_compute_state',store=True)

    market_price = fields.Float(string="Market Price", digits=(12, 2))
    p_contract_diff = fields.Float(string="P-Contract Differencial", digits=(12, 2))
    final_price = fields.Float(string="Final Price", digits=(12, 2), compute='_compute_amount')

    remainning_qty = fields.Float(string='Remainning Qty', compute='compute_remaning_qty')

    p_contract_id = fields.Many2one('s.contract',string="P Contract")
    number_of_bags = fields.Float(string="Number of bags")
    
