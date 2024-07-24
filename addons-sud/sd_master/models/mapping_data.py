# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class MappingProduct(models.Model):
    _name = 'mapping.product'

    grade = fields.Char(string="Grade")
    screen = fields.Char(string="Screen")
    code = fields.Char(string="Code")
    quality = fields.Char('Quality',)
    
    product_id = fields.Many2one('product.product', string="Product" , compute='product_id', store =True)
    
    def _product(self):
        for order in self:
            prdouct = self.env['product.product'].search([('default_code','=',order.code)],limit =1)
            order.product_id = prdouct and prdouct.id or False



class MappingPartner(models.Model):
    _name = 'mapping.partner'

    client_name = fields.Char(string="Client name")
    mapping = fields.Char(string="Mapping")
    patner_id = fields.Many2one('res.partner', string="Partner" )
    
    
    def _partner(self):
        for order in self:
            patner_ids = self.env['res.partner'].search(['|',('name','=',order.mapping),('shortname','=',order.mapping)])
            if len(patner_ids)>1:
                patner_ids = self.env['res.partner'].search(['|',('name','=',order.mapping),('shortname','=',order.mapping),('company_type','=','company')])
                
            order.patner_id = patner_ids and patner_ids.id or False
            
    

