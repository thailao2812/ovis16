# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from datetime import datetime
  
    
class FOBPSSManagement(models.Model):
    _inherit ="fob.pss.management"
    
    def update_pss_approved_for_s_p_allocate(self):
        for i in self:
            if i.x_traffic_contract:
                s_p_contract = self.env['sale.contract'].search([
                    ('x_is_bonded','=', True),
                    ('scontract_id.traffic_link_id','=',i.x_traffic_contract.id)
                ])
                for j in s_p_contract:
                    fob_pss = self.env['fob.pss.management'].search([
                    ('x_traffic_contract', '=', j.scontract_id.traffic_link_id.id),
                    ('pss_status', '=', 'approved')])
                    j.pss_approved = len(fob_pss)
            
                for j in s_p_contract:
                    fob_pss = self.env['fob.pss.management'].search([
                    ('x_traffic_contract', '=', j.scontract_id.traffic_link_id.id),
                    ('pss_status', '=', 'sent')])
                    j.pss_count_sent = len(fob_pss)

                for j in s_p_contract:
                    fob_pss = self.env['fob.pss.management'].search([
                    ('x_traffic_contract', '=', j.scontract_id.traffic_link_id.id),
                    ('pss_status', '=', 'rejected')])
                    j.pss_reject = len(fob_pss)
                
            
    
    @api.model
    def create(self, vals):
        new_id = super(FOBPSSManagement, self).create(vals)
        if 'pss_status' in vals:
            new_id.update_pss_approved_for_s_p_allocate()
        return new_id
    
    
    def write(self, vals):
        write_new_id = super(FOBPSSManagement, self).write(vals)
        if 'pss_status' in vals:
            self.update_pss_approved_for_s_p_allocate()
        
        return write_new_id
    
