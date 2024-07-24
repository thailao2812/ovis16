# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

class SaleContractLine(models.Model):
    _name = "sale.contract.line"
    _inherit = ['mail.thread']
    
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
                
    @api.depends('product_qty', 'price_unit', 'tax_id')
    def _compute_amount(self):
        for line in self:
            conversion = line.conversion or 1
            price = line.price_unit / conversion
            taxes = line.tax_id.compute_all(price, line.contract_id.currency_id, line.product_qty, product=line.product_id, partner=line.contract_id.partner_id)
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })
    
    contract_id = fields.Many2one('sale.contract', string='Contract Reference', ondelete='cascade', index=True, copy=False)
    name = fields.Text(string='Description', required=True)
    sequence = fields.Integer(string='Sequence', default=10)

    company_id = fields.Many2one(related='contract_id.company_id', string='Company', store=True, readonly=True)
    partner_id = fields.Many2one(related='contract_id.partner_id', store=True, string='Customer')
    
    state = fields.Selection(selection=[('draft', 'New'), ('approved', 'Approved'), ('done', 'Done'), ('cancel', 'Cancelled')],
         related='contract_id.state', string='Status', readonly=True, copy=False, store=True, default='draft')
    
    currency_id = fields.Many2one(related='contract_id.currency_id', store=True, string='Currency', readonly=True)
    
    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)], change_default=True, required=True)
    product_qty = fields.Float(string='Qty',  required=True, default=1.0)
    product_uom = fields.Many2one('uom.uom', string='UoM', required=True)
    price_unit = fields.Float('Unit Price', required=True, default=0.0)
    tax_id = fields.Many2many('account.tax', string='Taxes')
    
    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', readonly=True, store=True)
    price_tax = fields.Monetary(compute='_compute_amount', string='Taxes', readonly=True, store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total', readonly=True, store=True)
    conversion = fields.Float('Conversion', required=False,  default=1000,digits=(12, 0))

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

        # if self.contract_id.partner_id:
        #     vals['price_unit'] = self.env['account.tax']._fix_tax_included_price(product.price, product.taxes_id, self.tax_id)
        self.update(vals)
        return {'domain': domain}
    
    ######################   ned Contract ######################################################
    
    @api.depends('certificate_id','contract_id.shipping_id','contract_id.crop_id','product_id')
    def _compute_premium(self):
        for this in self:
            premium_id = self.env['mrp.bom.premium'].search([('crop_id','=', this.contract_id.crop_id.id)], limit=1)
            product_prem = premium_id.prem_ids.filtered(lambda x: x.product_id.id == this.product_id.id).premium or 0.0
            packing_prem = this.contract_id.shipping_id.shipping_ids.filtered(lambda r: r.product_id.id == this.product_id.id).packing_id.Premium or 0.0
            this.premium = this.certificate_id.premium + product_prem + packing_prem

    @api.depends('provisional_g2_price','premium','provisional_g2_diff','premium_adjustment')
    def _provisional_price(self):
        for sale in self:
            if sale.provisional_g2_price:
                sale.provisional_price = sale.premium + sale.provisional_g2_price + sale.provisional_g2_diff + sale.premium_adjustment
            else:
                sale.provisional_price = 0.0
    
    @api.depends('final_g2_price','premium','final_g2_diff','premium_adjustment')
    def _final_price(self):
        for sale in self:
            sale.price_unit = sale.premium + sale.final_g2_price + sale.final_g2_diff + sale.premium_adjustment
            
    certificate_id = fields.Many2one('ned.certificate', string='Certificate', ondelete='restrict')
    packing_id = fields.Many2one('ned.packing', string='Packing', ondelete='restrict')
    premium = fields.Float(string="Premium", compute='_compute_premium', store=True)
    premium_adjustment = fields.Float(string='Premium Adjustment')
    provisional_g2_price = fields.Float(string="Provisional G2 price",digits=(16, 2))
    provisional_g2_diff = fields.Float(string="Provisional G2 diff",digits=(16, 2))
    provisional_price = fields.Float(compute='_provisional_price',digits=(16, 2),store = True)
    
    final_g2_price = fields.Float(string = 'Final G2 price',digits=(16, 2))
    final_g2_diff = fields.Float(string = 'Final G2 diff',digits=(16, 2))
    price_unit = fields.Float(compute='_final_price',digits=(16, 2),store = True,string="Price")
    
    #########################################