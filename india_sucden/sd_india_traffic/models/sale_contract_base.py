# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError


class SaleContractLine(models.Model):
    _inherit = 'sale.contract.line'

    packing_cost = fields.Float(string='Packing Cost')
    cert_premium = fields.Float(string='Certificate Premium')
    differential = fields.Float(string='Additional Cost')



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
                        record.packing_cost = rec.scontract_id.contract_line[0].packing_cost
                        record.cert_premium = rec.scontract_id.contract_line[0].premium_cert
                        record.differential = rec.scontract_id.contract_line[0].differential
                        record.price_unit = (record.packing_cost + record.cert_premium +
                                             record.differential + mapped_p_number)
        return res
