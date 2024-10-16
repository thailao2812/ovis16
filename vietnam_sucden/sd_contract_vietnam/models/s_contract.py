# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

class SContract(models.Model):
    _inherit = "s.contract"
 
    eudr_check = fields.Boolean(string='Is EUDR', default=False)
    combine_check = fields.Boolean(string='Is Combined', default=False)
    cert_combine = fields.Many2many('ned.certificate', 'certificate_s_contract', 's_contract_id', 'certificate_id', string="Cer Combine",) 

    @api.onchange("eudr_check", "combine_check", 'contract_line.certificate_id')
    def onchange_cert_combine(self):
        if self.contract_line.certificate_id:
            cer_arr = []
            if self.eudr_check:
                if self.combine_check:
                    cer_list = self.env['ned.certificate'].search([('name','=like',self.contract_line.certificate_id.name + '-%')])
                    self.cert_combine = cer_list
                else:
                    cer_list = self.env['ned.certificate'].search(['|', ('name','=',self.contract_line.certificate_id.name),('name','=','EUDR')])
                    for cer in cer_list:
                        cer_arr.append(cer.id)
                self.cert_combine = cer_arr
            else:
                self.combine_check = False
                self.cert_combine = self.contract_line.certificate_id

# class ShippingInstruction(models.Model):
#     _inherit = "shipping.instruction"

#     cert_combine = fields.Many2many('ned.certificate', 'certificate_s_contract', 's_contract_id', 'certificate_id', string="Cer Combine",) 
