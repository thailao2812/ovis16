# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError

class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'
    
    sequence_id = fields.Many2one('ir.sequence', string='Sequence Receipt', readonly=True, copy=False)
    
    @api.model
    def _create_sequence(self, vals, refund=False):
        """ Create new no_gap entry sequence for every new Journal"""
        seq = {
            'name': vals['name'] + 'Receipt',
            'implementation': 'standard',
            'prefix': 'GRN-'+ _(vals['code']),
            'padding': 5,
            'number_increment': 1,
            'use_date_range': False,
            'date_get':'1',
        }
        if 'company_id' in vals:
            seq['company_id'] = vals['company_id']
        return self.env['ir.sequence'].create(seq)
    
    @api.model
    def create(self, vals):
        result = super(StockWarehouse, self).create(vals)
        if not vals.get('sequence_id'):
            result.sequence_id = self.sudo()._create_sequence(vals).id
        return result
    
    def write(self, vals):
        #THANH: self is an array so need to for record in self
        for record in self:
            if not record.sequence_id and not vals.get('sequence_id'):
                seq = {
                    'name': self.name,
                    'implementation': 'standard',
                    'prefix': 'GRN-'+ _(record.code),
                    'padding': 5,
                    'number_increment': 1,
                    'use_date_range': False,
                    'date_get':'1',
                }
                if record.company_id:
                    seq['company_id'] = record.company_id.id
                record.sequence_id = self.env['ir.sequence'].sudo().create(seq).id  
                  
        return super(StockWarehouse,self).write(vals)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    