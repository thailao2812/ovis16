# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError


class SaleContractLine(models.Model):
    _inherit = 'sale.contract.line'

    packing_cost = fields.Float(string='Packing Cost')
    cert_premium = fields.Float(string='Certificate Premium')
    differential = fields.Float(string='Additional Cost')
    type = fields.Selection(related='contract_id.type', store=True)

    @api.onchange('packing_id', 'product_qty', 'type')
    def onchange_packing_id(self):
        if self.packing_id:
            if self.type == 'export':
                self.packing_cost = self.packing_id.Premium
            else:
                self.packing_cost = 0

    @api.onchange('certificate_id', 'product_id')
    def onchange_certificate_id(self):
        if self.certificate_id:
            line_premium = self.certificate_id.sale_premium_line.filtered(
                lambda x: x.item_group_id.id == self.product_id.item_group_id.id)
            if line_premium:
                self.cert_premium = line_premium.sale_premium
            else:
                self.cert_premium = 0
        else:
            self.cert_premium = 0


class SaleContract(models.Model):
    _inherit = 'sale.contract'

    @api.model
    def create(self, vals):
        res = super(SaleContract, self).create(vals)
        if res.type == 'local':
            res.name = self.env['ir.sequence'].next_by_code('sale.contract.india.local.base')
        if res.type == 'export':
            res.name = self.env['ir.sequence'].next_by_code('sale.contract.india.export.base')
        return res

    def button_load(self):
        res = super(SaleContract, self).button_load()
        for rec in self:
            if rec.type == 'export':
                if rec.scontract_id:
                    mapped_p_number = 0
                    psc_to_sc_link = self.env['psc.to.sc.linked'].search([
                        ('state_allocate', '=', 'submit'),
                        ('s_contract', '=', rec.scontract_id.id)
                    ])
                    if psc_to_sc_link:
                        mapped_p_number = sum(psc_to_sc_link.mapped('sale_contract_id.price_unit'))
                    for record in rec.contract_line:
                        record.onchange_certificate_id()
                        record.onchange_packing_id()
                        record.price_unit = (record.packing_cost + record.cert_premium +
                                             record.differential + mapped_p_number)
        return res
