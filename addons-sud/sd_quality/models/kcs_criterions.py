# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from datetime import datetime


class KCSCriterions(models.Model):
    _name = "kcs.criterions"
    _inherit = ['mail.thread']
    _order = 'id asc'
    
    
    crop_id = fields.Many2one('ned.crop', string='Crop',  )
    is_factory = fields.Boolean(string="Is Factory", default=False, copy = False)
    is_grn = fields.Boolean(string="Is Grn", default=False, copy = False)
    is_grp = fields.Boolean(string="Is Grp", default=False, copy = False)
    
    name = fields.Char(string="Name", required=True, copy=False, default="New", readonly=True,  states={'draft': [('readonly', False)]})
    from_date = fields.Date(string="From Date", required=True, default=fields.Datetime.now, copy=False, readonly=True,  states={'draft': [('readonly', False)]})
    to_date = fields.Date(string="TO Date", default=fields.Datetime.now, copy=False, readonly=True,  states={'draft': [('readonly', False)]})
    state = fields.Selection([("draft", "New"),("approved", "Approved"),("cancel", "Cancelled")], string="Status", readonly=True, copy=False, index=True, default='draft')
    categ_id = fields.Many2one("product.category", string="Category", readonly=True,  states={'draft': [('readonly', False)]}, domain=[('parent_id','!=',False)])
    product_id = fields.Many2one("product.product", string="Product", readonly=True , required=False, states={'draft': [('readonly', False)]})
    special = fields.Boolean(string='Special',default=False)
    origin = fields.Char(string='Source Document')
    note = fields.Text(string="Notes")
    ksc_line_ids = fields.One2many("kcs.criterions.line", "ksc_id", "KCS Line", readonly=True, states={'draft': [('readonly', False)]})
    
    create_date = fields.Date(string='Creation Date', readonly=True, index=True, default=fields.Datetime.now, copy=False)
    create_uid = fields.Many2one('res.users', 'Responsible', readonly=True , default=lambda self: self._uid, copy=False)
    date_approve = fields.Date('Approval Date', readonly=True, copy=False)
    user_approve = fields.Many2one('res.users', string='User Approve', readonly=True, copy=False)
    
    broken_standard_ids = fields.One2many("broken.standard", "criterion_id", string="Broken",readonly=True, states={'draft': [('readonly', False)]}, copy=True)
    brown_standard_ids = fields.One2many("brown.standard", "criterion_id", string="Brown",readonly=True, states={'draft': [('readonly', False)]}, copy=True)
    mold_standard_ids = fields.One2many("mold.standard", "criterion_id", string="Mold",readonly=True, states={'draft': [('readonly', False)]}, copy=True)
    foreign_matter_ids = fields.One2many("foreign.matter", "criterion_id", string="Foreign Matter",readonly=True, states={'draft': [('readonly', False)]}, copy=True)
    
    ligh_burnded_bean_ids = fields.One2many("ligh.burnded.bean", "criterion_id", string="Ligh Burnded Bean",readonly=True, states={'draft': [('readonly', False)]}, copy=True)
    
    insect_bean_ids = fields.One2many("insect.bean", "criterion_id", string="Insect Matter",readonly=True, states={'draft': [('readonly', False)]}, copy=True)
    over_screen12_ids = fields.One2many("over.screen12", "criterion_id", string="Over Screen 12",readonly=True, states={'draft': [('readonly', False)]}, copy=True)
    excelsa_standard_ids = fields.One2many("excelsa.standard", "criterion_id", string="Excelsa",readonly=True, states={'draft': [('readonly', False)]}, copy=True)
    burned_deduct_ids = fields.One2many("burned.deduct", "criterion_id", string="Burned_",readonly=True, states={'draft': [('readonly', False)]}, copy=True)
    
    standard_excelsa = fields.Float(string="Excelsa_%",  digits=(12, 2),readonly=True, states={'draft': [('readonly', False)]})
    percent_excelsa = fields.Float(string="Percent", digits=(12, 2),readonly=True, states={'draft': [('readonly', False)]})
    
    
    
    standard_screen18_16 = fields.Float(string="OverScreen16_%",  digits=(12, 2),readonly=True, states={'draft': [('readonly', False)]})
    percent_screen18_16 = fields.Float(string="Percent",  digits=(12, 2),readonly=True, states={'draft': [('readonly', False)]})
    standard_screen13 = fields.Float(string="OverScreen13_%",  digits=(12, 2),readonly=True, states={'draft': [('readonly', False)]})
    percent_screen13 = fields.Float(string="Percent",  digits=(12, 2),readonly=True, states={'draft': [('readonly', False)]})
    
    standard_screen18 = fields.Float(string="OverScreen18_%",  digits=(12, 2),readonly=True, states={'draft': [('readonly', False)]})
    percent_screen18 = fields.Float(string="Percent",  digits=(12, 2),readonly=True, states={'draft': [('readonly', False)]})
    standard_screen19 = fields.Float(string="OverScreen19_%",  digits=(12, 2),readonly=True, states={'draft': [('readonly', False)]})
    percent_screen19 = fields.Float(string="Percent",  digits=(12, 2),readonly=True, states={'draft': [('readonly', False)]})
    standard_screen20 = fields.Float(string="OverScreen20_%",  digits=(12, 2),readonly=True, states={'draft': [('readonly', False)]})
    percent_screen20 = fields.Float(string="Percent",  digits=(12, 2),readonly=True, states={'draft': [('readonly', False)]})
    
    standard_burned = fields.Float(string="Burned_%",  digits=(12, 2),readonly=True, states={'draft': [('readonly', False)]})
    percent_burned = fields.Float(string="Percent",  digits=(12, 2),readonly=True, states={'draft': [('readonly', False)]})
    percent_fm = fields.Float(string="Fm",default="0.01",  digits=(12, 2),readonly=True, states={'draft': [('readonly', False)]}, copy=True)
    
    degree_mc = fields.Float(string="Degree Mc" , digits=(12, 2),readonly=True, states={'draft': [('readonly', False)]}, copy=True)
    finished_products = fields.Boolean('Finished Products',readonly=True, states={'draft': [('readonly', False)]})
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    active = fields.Boolean(string="Actived", default= True)
    type_warehouse = fields.Selection([('bonded', 'Bonded'), ('non_bonded', 'Non Bonded'),
         ('processing', 'Processing')], string="Type", default='bonded', required=True)
    
    reject_rule = fields.Boolean(string='Reject Rule',default=False)
    
    @api.onchange('crop_id')
    def onchang_crop_id(self):
        if self.crop_id:
            self.from_date = self.crop_id.start_date
            self.to_date = self.crop_id.to_date
        
    
    @api.onchange('type_warehouse')
    def onchang_type_warehouse(self):
        warehouse_ids = False
        if self.type_warehouse == 'bonded':
            warehouse_ids = self.env['stock.warehouse'].search([('x_is_bonded','=',True)])
        elif self.type_warehouse == 'non_bonded':
            warehouse_ids = self.env['stock.warehouse'].search([('x_is_bonded','!=',True)])
        else:
            warehouse_ids = self.env['stock.warehouse'].search([])
            
        self.x_warehouse_id = warehouse_ids and warehouse_ids.ids or False
        
    
    @api.model
    def _domain_warehouse(self):
        return "[('id', 'in', %s)]" % self.env.user._warehouses_domain()
    
    x_warehouse_id = fields.Many2many('stock.warehouse', 'kcs_rule_warehouse_rel', 'rule_id', 'warehouse_id', 
                              string='Warehouse' , readonly=True, states={'draft': [('readonly', False)]} , domain=lambda self: self._domain_warehouse())
    
    mc_line = fields.One2many('kcs.criterions.mc', 'criterion_id', string='Degree Mc')
    
    
    def unlink(self):
        for kcs in self:
            if kcs.state not in ('draft', 'cancel'):
                raise UserError(_('You can only delete draft or cancel.'))
        return super(KCSCriterions, self).unlink()
    
    # @api.constrains('name')
    # def _check_name(self):
    #     if self.name:
    #         criterions_ids = self.search([('name', '=', self.name), ('id', '!=', self.id)])
    #         if criterions_ids:
    #             raise UserError(_("KCS Criterions (%s) was exist.") % (self.name))
    
        
    def button_approve(self): 
        if self.special:
            self.write({'state': 'approved', 'user_approve': self.env.uid,'date_approve': datetime.now()})
            return True
        
        if self.product_id:
            for criterions in  self.search([('id','!=',self.id),('state', '=', 'approved'), ('product_id','=',self.product_id.id), ('type_warehouse','=',self.type_warehouse)]): 
                if criterions.from_date <= self.from_date and self.from_date <= criterions.to_date:
                    raise UserError(_("KCS Criterions (%s) was exist. Date (%s - %s)") % (criterions.name,criterions.from_date,criterions.to_date))
                if criterions.from_date <= self.to_date and  self.to_date <= criterions.to_date:
                    raise UserError(_("KCS Criterions (%s) was exist. Date (%s - %s) ") % (criterions.name,criterions.from_date,criterions.to_date))
                    
                if self.from_date <= criterions.from_date and  criterions.from_date <= self.to_date:
                    raise UserError(_("KCS Criterions (%s) was exist. Date (%s - %s) ") % (criterions.name,criterions.from_date,criterions.to_date))
                if self.from_date <= criterions.to_date and  criterions.to_date <= self.to_date:
                    raise UserError(_("KCS Criterions (%s) was exist. Date (%s - %s) ") % (criterions.name,criterions.from_date,criterions.to_date))
                
            self.write({'state': 'approved', 'user_approve': self.env.uid,'date_approve': datetime.now()})
            return True
        
        if self.categ_id:
            kcs_criterions_ids =[]
            sql ='''
                SELECT id FROM
                    kcs_criterions
                    WHERE
                        state = 'approved'
                        and categ_id = %s
                        and product_id is null
                        and id != %s
            '''%(self.categ_id.id,self.id)
            self.env.cr.execute(sql)
            for line in self.env.cr.dictfetchall():
                kcs_criterions_ids.append(line['id'])
            if kcs_criterions_ids:
                for criterions in  self.browse(kcs_criterions_ids): 
                    if criterions.from_date <= self.from_date and  self.from_date <= criterions.to_date:
                        raise UserError(_("KCS Criterions (%s) was exist. Date (%s - %s)") % (criterions.name,criterions.from_date,criterions.to_date))
                    if criterions.from_date <= self.to_date and  self.to_date <= criterions.to_date:
                        raise UserError(_("KCS Criterions (%s) was exist. Date (%s - %s) ") % (criterions.name,criterions.from_date,criterions.to_date))
                    
                    if self.from_date <= criterions.from_date and  criterions.from_date <= self.to_date:
                        raise UserError(_("KCS Criterions (%s) was exist. Date (%s - %s) ") % (criterions.name,criterions.from_date,criterions.to_date))
                    if self.from_date <= criterions.to_date and  criterions.to_date <= self.to_date:
                        raise UserError(_("KCS Criterions (%s) was exist. Date (%s - %s) ") % (criterions.name,criterions.from_date,criterions.to_date))
                
        self.write({'state': 'approved', 'user_approve': self.env.uid,'date_approve': datetime.now()})
        return True
        
    def button_cancel(self):
        self.write({'state': 'cancel', 'date_cancel': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
    
    def button_draft(self):
        self.write({'state': 'draft'})
        
        
    
class KCSCriterionsLine(models.Model):
    _name = "kcs.criterions.line"
    _order = 'id asc'
    
    @api.model
    def _get_sequence(self):
        seq = 1
        for kcs_line in self:
            if not kcs_line.ids:
                return 
            kcs_line.sequence = seq
            seq += 1
    
    name = fields.Char(string="Description")
    sequence = fields.Integer(compute="_get_sequence", string="Sequence", store=False, )
    check_indicators = fields.Char(string='Check Indicators', required=True)
    value = fields.Float(string='Value', required=True)
    type = fields.Selection([('bigger', 'Bigger than the reference value'), ('reference', 'By reference value'),
         ('smaller', 'Smaller than the reference value')], string="Type", default='reference', required=True)
    description = fields.Text(string="Description")
    ksc_id = fields.Many2one("kcs.criterions", string="KCS Criterions", ondelete='cascade', index=True, copy=False)
    

    
    