# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from datetime import datetime
import xlrd
import base64
from xlrd import open_workbook


class MrpBomPremium(models.Model):
    _name = 'mrp.bom.premium'
    _description = 'Mrp Bom Premium'
    _order = 'id desc'
    
    name = fields.Char(string="Name", required=True)
    crop_id = fields.Many2one('ned.crop', string='Crop', required=False)
    active = fields.Boolean(string="Active",default="active")
    prem_ids = fields.One2many('mrp.bom.premium.line','prem_id', string='Crop', required=False)
    file = fields.Binary('File', help='Choose file Excel')
    file_name =  fields.Char('Filename', readonly=True)
    standard_cost = fields.Monetary(string='Standard Cost',currency_field='com_currency_id', default=16.35)
    company_id  = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)
    com_currency_id = fields.Many2one('res.currency', related='company_id.currency_id',string="Currency", readonly=True)
    bom_id = fields.Many2one('mrp.bom', string='Bom', required=False)
    
    def copy(self, default=None):
        self.ensure_one()
        result = super(MrpBomPremium, self).copy(default={})
        for line in self.prem_ids:
            line.copy(default={'prem_id': result.id})
        return result
    
    def import_file(self):
        flag = False
        for this in self:
            sql ='''
                DELETE FROM  Mrp_Bom_Premium_Line where prem_id = %s
            '''%(this.id)
            self.env.cr.execute(sql)
            
            try:
                recordlist = base64.decodestring(this.file)
                excel = xlrd.open_workbook(file_contents = recordlist)
                sh = excel.sheet_by_index(0)
            except e:
                raise UserError(_('Warning !!!'))
            if sh:
                for row in range(sh.nrows):
                    if row > 0:
                        product_code = sh.cell(row,1).value or False
                        if not product_code:
                            continue
                        if product_code =='QualityCode':
                            flag =True
                            continue
                            
                        if flag:
                            premium = sh.cell(row,16).value or 0.0
                            if isinstance(premium, float):
                                premium = float(premium)
                                premium = round(premium,0)
                                premium = str(premium)
                            product_id = self.env['product.product'].search([('default_code','=', product_code)],limit =1)
                            if not product_id:
                                continue
                            product_uom = self.env['product.uom'].search([('name','=', 'kg')],limit =1)
                            try:
                                self.env['mrp.bom.premium.line'].create({'prem_id':this.id,'product_id':product_id.id,'product_uom':product_uom.id,'premium':premium})
                            except e:
                                raise UserError(_('Warning !!!'))

                            
    
class MrpBomPremiumLine(models.Model):
    _name= 'mrp.bom.premium.line'
    _description = 'Mrp Bom Premium Line'
    _order = 'id desc'
    
    prem_id = fields.Many2one('mrp.bom.premium', required=False)
    product_id = fields.Many2one('product.product',string="Product", required=True)
    product_uom = fields.Many2one('uom.uom',string="UoM", required=True)
    premium = fields.Float(string='Prem/Disct')
    mc = fields.Float(string='MC')
    fm = fields.Float(string='FM')
    black = fields.Float(string='Black')
    broken = fields.Float(string='Broken')
    brown = fields.Float(string='Brown')
    mold = fields.Float(string='Mold')
    cherry = fields.Float(string='Cherry')
    excelsa = fields.Float(string='Excelsa')
    screen20 = fields.Float(string='Screen20')
    screen19 = fields.Float(string='Screen19')
    screen18 = fields.Float(string='Screen18')
    screen16 = fields.Float(string='Screen16')
    screen13 = fields.Float(string='Screen13')
    belowsc12 = fields.Float(string='Below12')
    burned = fields.Float(string='Burned')
    eaten = fields.Float(string='Insect')
    immature = fields.Float(string='Immature')
    
    flag = fields.Boolean(string='Flag',default=False)

    


    
    
    
    
    
    

