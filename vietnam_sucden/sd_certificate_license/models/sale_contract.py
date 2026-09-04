# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

class SaleContract(models.Model):
    _inherit = "sale.contract"

    product_prem = fields.Float('Product Premium', compute='_compute_premium')
    packing_prem = fields.Float('Packing Premium', compute='_compute_premium')
    cert_prem = fields.Float('Certificate Premium', compute='_compute_premium')
    total_prem = fields.Float('Total Premium', compute='_compute_premium')

    @api.depends('certificate_id_list','shipping_id','crop_id','contract_line.product_id')
    def _compute_premium(self):
        for this in self:
            if this.contract_line:
                for line in this.contract_line:
                    premium_id = self.env['mrp.bom.premium'].search([('crop_id','=', this.crop_id.id)], limit=1)
                    product_prem = premium_id.prem_ids.filtered(lambda x: x.product_id.id == line.product_id.id).premium or 0.0
                    packing_prem = this.shipping_id.shipping_ids.filtered(lambda r: r.product_id.id == line.product_id.id).packing_id.Premium or 0.0
                    cert_prem = sum(this.certificate_id_list.mapped('premium')) or 0.0
                    
                    this.product_prem = product_prem
                    this.packing_prem = packing_prem
                    this.cert_prem = cert_prem
                    this.total_prem = cert_prem + product_prem + packing_prem
            else:
                this.product_prem = 0.0
                this.packing_prem = 0.0
                this.cert_prem = 0.0
                this.total_prem = 0.0

    def button_load(self):
        if self.shipping_id:
            self.certificate_id_list = [(6, 0, [x.id for x in self.shipping_id.certificated_ids])]
            self.license_certificate_ids = [(6, 0, [x.license_id.id for x in self.shipping_id.license_allocation_ids])]
            self.contract_line.unlink()
            product_qty = new_qty = 0.0
            val ={
                    'scontract_id':self.shipping_id.contract_id and self.shipping_id.contract_id.id or False,
                    'partner_id':self.shipping_id.partner_id and self.shipping_id.partner_id.id or False,
                    'currency_id':self.shipping_id.contract_id.currency_id and self.shipping_id.contract_id.currency_id.id or False,
                    'port_of_loading': self.shipping_id.port_of_loading and self.shipping_id.port_of_loading.id or False,
                    'port_of_discharge': self.shipping_id.port_of_discharge and self.shipping_id.port_of_discharge.id or False,
                    'weights':self.shipping_id.contract_id and self.shipping_id.contract_id.weights or False,
                    'deadline': self.shipping_id.shipment_date
                }
            self.write(val)
                        
            for shipping in self.shipping_id.shipping_ids:
                nvs_line = self.env['sale.contract.line'].search([('state','!=','cancel'),('product_id','=',shipping.product_id.id),('contract_id.shipping_id','=',self.shipping_id.id)])
                product_qty = sum(nvs_line.mapped('product_qty')) or 0.0
                new_qty = shipping.product_qty - product_qty
                var = {'contract_id': self.id or False, 'name': shipping.name or False, 
                        'product_id': shipping.product_id.id or False,
                        'tax_id': [(6, 0, [x.id for x in shipping.tax_id])] or False, 'price_unit': shipping.price_unit or 0.0,
                        'product_qty': new_qty or 0.0, 'product_uom': shipping.product_uom.id or False,
                        'state': 'draft', 'certificate_id': shipping.certificate_id.id or False, 'packing_id': shipping.packing_id.id or False}
                self.env['sale.contract.line'].create(var)
                
        return True

class SaleContractLine(models.Model):
    _inherit = "sale.contract.line"
    
    @api.depends('certificate_id','contract_id.shipping_id','contract_id.crop_id','product_id','contract_id.certificate_id_list')
    def _compute_premium(self):
        for this in self:
            premium_id = self.env['mrp.bom.premium'].search([('crop_id','=', this.contract_id.crop_id.id)], limit=1)
            product_prem = premium_id.prem_ids.filtered(lambda x: x.product_id.id == this.product_id.id).premium or 0.0
            packing_prem = this.contract_id.shipping_id.shipping_ids.filtered(lambda r: r.product_id.id == this.product_id.id).packing_id.Premium or 0.0
            cert_prem = sum(this.contract_id.certificate_id_list.mapped('premium')) or 0.0
            this.premium = cert_prem + product_prem + packing_prem

    # certificated_ids = fields.Many2many(related='contract_id.certificate_id_list', string='Cer Compliant')
