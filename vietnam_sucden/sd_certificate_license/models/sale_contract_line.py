# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

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
            