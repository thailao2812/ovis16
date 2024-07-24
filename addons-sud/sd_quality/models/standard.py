# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

class KCSCriterionsMC(models.Model):
    _name = "kcs.criterions.mc"

    name = fields.Float(string='Degree MC')
    percent = fields.Float(string='Percent (%)')
    criterion_id = fields.Many2one('kcs.criterions', string='Criterions')
    rule = fields.Selection([('addition','Addition (+)'),('subtraction','Subtraction (-)')], string="Rule", default="subtraction", required=False)
    
class InspectorsKCS(models.Model):
    _name = "x_inspectors.kcs"

    name = fields.Char(string='Inspector', size=256)


class BurnedDeduct(models.Model):
    _name = "burned.deduct"
    _oder = "id desc"

    name = fields.Char(string="Range", default="New")
    range_start = fields.Float(string="From (%)", default=3, digits=(12, 2))
    range_end = fields.Float(string="To (%)", default=6, digits=(12, 2))

    subtract = fields.Boolean(string="Subtract", default=True, copy=False)
    percent = fields.Float(string="Percent (%)", default=5, digits=(12, 2))
    criterion_id = fields.Many2one("kcs.criterions",string="KCS Criterion", ondelete='cascade', index=True, copy=False)
    compares = fields.Selection([('<','Smaller values'),('<=','Smaller or equal values')], string="Type Compares", default="<", required=True)


    @api.constrains('range_start')
    def _check_range_from(self):
        for i in self:
            if i.range_start < 0:
                raise UserError(_("Burned Standard: Range start do not smaller 0."))
            if i.range_start > i.range_end:
                raise UserError(_("Burned Standard: Range start do not bigger the range ended."))

    @api.constrains('range_end')
    def _check_range_end(self):
        for i in self:
            if i.range_end < i.range_start:
                raise UserError(_("Burned Standard: Range end do not bigger the range started."))
            if i.range_start > 100:
                raise UserError(_("Burned Standard: Range end do  not bigger 100."))
            
    

class BrokenStandard(models.Model):
    _name = "broken.standard"
    _oder = "range_end desc,id desc"
    
    name = fields.Char(string="Range", default="New")
    range_start = fields.Float(string="From (%)", default=5, digits=(12, 2))
    range_end = fields.Float(string="To (%)", default=7, digits=(12, 2))
    
    percent = fields.Float(string="Percent (%)", default=0.5, digits=(12, 2))
    criterion_id = fields.Many2one("kcs.criterions",string="KCS Criterion", ondelete='cascade', index=True, copy=False)
    subtract = fields.Boolean(string="Subtract", default=True)
    rule = fields.Selection([('addition','Addition (+)'),('subtraction','Subtraction (-)')], string="Rule", default="subtraction", required=False)
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New'):
            if vals.get('range_start', False) and vals.get('range_end', False):
                name = 'Range ' + str(vals.get('range_start', False)) + ' - ' + str(vals.get('range_end', False))
            elif not vals.get('range_start', False) and vals.get('range_end', False):
                name = 'Range 0' + '-' + str(vals.get('range_end', False))
            vals['name'] = name
        result = super(BrokenStandard, self).create(vals)
        return result
    
    @api.constrains('percent')
    def _check_percent(self):
        for i in self:
            if i.percent < 0:
                raise UserError(_("Broken Standard: Percent do  not smaller 0."))
            elif i.percent > 100:
                raise UserError(_("Broken Standard: Percent do  not bigger 100."))
    
    @api.constrains('range_start')
    def _check_range_from(self):
        for i in self:
            if i.range_start < 0:
                raise UserError(_("Broken Standard: Range start do not smaller 0."))
            if i.range_start > i.range_end:
                raise UserError(_("Broken Standard: Range start do not bigger the range ended."))
        
    @api.constrains('range_end')
    def _check_range_end(self):
        for i in self:
            if i.range_end < i.range_start:
                raise UserError(_("Broken Standard: Range end do not bigger the range started."))
            if i.range_start > 100:
                raise UserError(_("Broken Standard: Range end do  not bigger 100."))
        
class BrownStandard(models.Model):
    _name = "brown.standard"
    _oder = "range_end desc,id desc"
    
    name = fields.Char(string="Range", default="New")
    range_start = fields.Float(string="From (%)", default=5, digits=(12, 2))
    range_end = fields.Float(string="To (%)", default=7, digits=(12, 2))
    
    percent = fields.Float(string="Percent (%)", default=50, digits=(12, 2))
    values = fields.Float(string="Values Other", default=1, digits=(12, 2))
    criterion_id = fields.Many2one("kcs.criterions",string="KCS Criterion", ondelete='cascade', index=True, copy=False)
    subtract = fields.Boolean(string="Subtract", default=True, copy=False)
    check_values = fields.Boolean(string="Enter Values Other", default=True, copy=False)
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New'):
            if vals.get('range_start', False) and vals.get('range_end', False):
                name = 'Range ' + str(vals.get('range_start', False)) + ' - ' + str(vals.get('range_end', False))
            elif not vals.get('range_start', False) and vals.get('range_end', False):
                name = 'Range 0' + ' - ' + str(vals.get('range_end', False))
            vals['name'] = name
        result = super(BrownStandard, self).create(vals)
        return result
    
    @api.constrains('percent')
    def _check_percent(self):
        if self.percent < 0:
            raise UserError(_("Brown Standard: Percent do  not smaller 0."))
        elif self.percent > 100:
            raise UserError(_("Brown Standard: Percent do  not bigger 100."))
    
    @api.constrains('range_start')
    def _check_range_from(self):
        for i in self:
            if i.range_start < 0:
                raise UserError(_("Brown Standard: Range start do not smaller 0."))
            if i.range_start > i.range_end:
                raise UserError(_("Brown Standard: Range start do not bigger the range ended."))
        
    @api.constrains('range_end')
    def _check_range_end(self):
        for i in self:
            if i.range_end < i.range_start:
                raise UserError(_("Brown Standard: Range end do not bigger the range started."))
            if i.range_start > 100:
                raise UserError(_("Brown Standard: Range end do  not bigger 100."))

class ForeignMatter(models.Model):
    _name = "foreign.matter"
    _oder = "range_end desc,id desc"
    
    name = fields.Char(string="Range", default="New")
    range_start = fields.Float(string="From (%)", default=3, digits=(12, 2))
    range_end = fields.Float(string="To (%)", default=6, digits=(12, 2))
    
    subtract = fields.Boolean(string="Subtract", default=True, copy=False)
    percent = fields.Float(string="Percent (%)", default=5, digits=(12, 2))
    criterion_id = fields.Many2one("kcs.criterions",string="KCS Criterion", ondelete='cascade', index=True, copy=False)
    compares = fields.Selection([('<','Smaller values'),('<=','Smaller or equal values')], string="Type Compares", default="<", required=True)
    rule = fields.Selection([('addition','Addition (+)'),('subtraction','Subtraction (-)')], string="Rule", default="subtraction", required=False)

class LighBurndedBean(models.Model):
    _name = "ligh.burnded.bean"
    _oder = "range_end desc,id desc"
    
    name = fields.Char(string="Range", default="New")
    range_start = fields.Float(string="From (%)", default=3, digits=(12, 2))
    range_end = fields.Float(string="To (%)", default=6, digits=(12, 2))
    
    percent = fields.Float(string="Percent (%)", default=5, digits=(12, 2))
    criterion_id = fields.Many2one("kcs.criterions",string="KCS Criterion", ondelete='cascade', index=True, copy=False)
    compares = fields.Selection([('<','Smaller values'),('<=','Smaller or equal values')], string="Type Compares", default="<", required=True)
    rule = fields.Selection([('pass','Pass'),('rejected','Rejected')], string="Rule", default="subtraction", required=False)
    
#     @api.constrains('percent')
#     def _check_percent(self):
#         if self.percent < 0:
#             raise UserError(_("Brown Standard: Percent do  not smaller 0."))
#         elif self.percent > 100:
#             raise UserError(_("Brown Standard: Percent do  not bigger 100."))
    
    @api.constrains('range_start')
    def _check_range_from(self):
        for i in self:
            if i.range_start < 0:
                raise UserError(_("Brown Standard: Range start do not smaller 0."))
            if i.range_start > i.range_end:
                raise UserError(_("Brown Standard: Range start do not bigger the range ended."))
        
    @api.constrains('range_end')
    def _check_range_end(self):
        for i in self:
            if i.range_end < i.range_start:
                raise UserError(_("Brown Standard: Range end do not bigger the range started."))
            if i.range_start > 100:
                raise UserError(_("Brown Standard: Range end do  not bigger 100."))

class IndicatorKCS(models.Model):
    _name = "indicator.kcs"
    
    check_indicators = fields.Char(string="Check Indicators", required=True)
    standard = fields.Float(string="Standard", required=True)
    type = fields.Selection([('bigger', 'Bigger than the reference value'), ('reference', 'By reference value'),
         ('smaller', 'Smaller than the reference value')], string="Type", default='reference', required=True)
    measured_value = fields.Float(string="Measured Value", required=True)
    request_line_id = fields.Many2one("request.kcs.line", string="Request KCS Line", ondelete='cascade', index=True, copy=False)
    note = fields.Text(string="Note", copy=False)



class InsectBean(models.Model):
    _name = "insect.bean"
    _oder = "range_end desc,id desc"
    
    name = fields.Char(string="Range", default="New")
    range_start = fields.Float(string="From (%)", default=3, digits=(12, 2))
    range_end = fields.Float(string="To (%)", default=6, digits=(12, 2))
    
    percent = fields.Float(string="Percent (%)", default=5, digits=(12, 2))
    criterion_id = fields.Many2one("kcs.criterions",string="KCS Criterion", ondelete='cascade', index=True, copy=False)
    

class MoldStandard(models.Model):
    _name = "mold.standard"
    _oder = "range_end desc,id desc"
    
    name = fields.Char(string="Range", default="New")
    range_start = fields.Float(string="From (%)", default=3, digits=(12, 2))
    range_end = fields.Float(string="To (%)", default=6, digits=(12, 2))
    
    subtract = fields.Boolean(string="Subtract", default=True, copy=False)
    percent = fields.Float(string="Percent (%)", default=5, digits=(12, 2))
    criterion_id = fields.Many2one("kcs.criterions",string="KCS Criterion", ondelete='cascade', index=True, copy=False)
    compares = fields.Selection([('<','Smaller values'),('<=','Smaller or equal values')], string="Type Compares", default="<", required=True)
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New'):
            if vals.get('range_start', False) and vals.get('range_end', False):
                name = 'Range ' + str(vals.get('range_start', False)) + ' - ' + str(vals.get('range_end', False))
            elif not vals.get('range_start', False) and vals.get('range_end', False):
                name = 'Range 0' + ' - ' + str(vals.get('range_end', False))
            vals['name'] = name
        result = super(MoldStandard, self).create(vals)
        return result
    
    @api.constrains('percent')
    def _check_percent(self):
        for i in self:
            if i.percent < 0:
                raise UserError(_("Mold Standard: Percent do  not smaller 0."))
            elif i.percent > 100:
                raise UserError(_("Mold Standard: Percent do  not bigger 100."))
    
    @api.constrains('range_start')
    def _check_range_from(self):
        for i in self:
            if i.range_start < 0:
                raise UserError(_("Mold Standard: Range start do not smaller 0."))
            if i.range_start > self.range_end:
                raise UserError(_("Mold Standard: Range start do not bigger the range ended."))
        
    @api.constrains('range_end')
    def _check_range_end(self):
        for i in self:
            if i.range_end < i.range_start:
                raise UserError(_("Mold Standard: Range end do not bigger the range started."))
            if i.range_start > 100:
                raise UserError(_("Mold Standard: Range end do  not bigger 100."))

class OverScreen12(models.Model):
    _name = "over.screen12"
    _oder = "range_end desc,id desc"
    
    name = fields.Char(string="Range", default="New")
    range_start = fields.Float(string="From (%)", default=3, digits=(12, 2))
    range_end = fields.Float(string="To (%)", default=6, digits=(12, 2))
    
    subtract = fields.Boolean(string="Subtract", default=True, copy=False)
    percent = fields.Float(string="Percent (%)", default=5, digits=(12, 2))
    criterion_id = fields.Many2one("kcs.criterions",string="KCS Criterion", ondelete='cascade', index=True, copy=False)
    compares = fields.Selection([('<','Smaller values'),('<=','Smaller or equal values')], string="Type Compares", default="<", required=True)
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New'):
            if vals.get('range_start', False) and vals.get('range_end', False):
                name = 'Range ' + str(vals.get('range_start', False)) + ' - ' + str(vals.get('range_end', False))
            elif not vals.get('range_start', False) and vals.get('range_end', False):
                name = 'Range 0' + ' - ' + str(vals.get('range_end', False))
            vals['name'] = name
        result = super(OverScreen12, self).create(vals)
        return result
    
    @api.constrains('percent')
    def _check_percent(self):
        for i in self:
            if i.percent < 0:
                raise UserError(_("Over Screen 12: Percent do  not smaller 0."))
            elif i.percent > 100:
                raise UserError(_("Over Screen 12: Percent do  not bigger 100."))
    
    @api.constrains('range_start')
    def _check_range_from(self):
        for i in self:
            if i.range_start < 0:
                raise UserError(_("Over Screen 12: Range start do not smaller 0."))
            if i.range_start > i.range_end:
                raise UserError(_("Over Screen 12: Range start do not bigger the range ended."))
        
    @api.constrains('range_end')
    def _check_range_end(self):
        for i in self:
            if i.range_end < self.range_start:
                raise UserError(_("Over Screen 12: Range end do not bigger the range started."))
            if i.range_start > 100:
                raise UserError(_("Over Screen 12: Range end do  not bigger 100."))

class ExcelsaStandard(models.Model):
    _name = "excelsa.standard"
    _oder = "range_end desc,id desc"
    
    name = fields.Char(string="Range", default="New")
    range_start = fields.Float(string="From (%)", default=3, digits=(12, 2))
    range_end = fields.Float(string="To (%)", default=6, digits=(12, 2))
    
    subtract = fields.Boolean(string="Subtract", default=True, copy=False)
    percent = fields.Float(string="Percent (%)", default=5, digits=(12, 2))
    criterion_id = fields.Many2one("kcs.criterions",string="KCS Criterion", ondelete='cascade', index=True, copy=False)
    compares = fields.Selection([('<','Smaller values'),('<=','Smaller or equal values')], string="Type Compares", default="<", required=True)
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New'):
            if vals.get('range_start', False) and vals.get('range_end', False):
                name = 'Range ' + str(vals.get('range_start', False)) + ' - ' + str(vals.get('range_end', False))
            elif not vals.get('range_start', False) and vals.get('range_end', False):
                name = 'Range 0' + ' - ' + str(vals.get('range_end', False))
            vals['name'] = name
        result = super(ExcelsaStandard, self).create(vals)
        return result
    
    @api.constrains('percent')
    def _check_percent(self):
        for i in self:
            if i.percent < 0:
                raise UserError(_("Excelsa Standard: Percent do  not smaller 0."))
            elif i.percent > 100:
                raise UserError(_("Excelsa Standard: Percent do  not bigger 100."))
    
    @api.constrains('range_start')
    def _check_range_from(self):
        for i in self:
            if i.range_start < 0:
                raise UserError(_("Excelsa Standard: Range start do not smaller 0."))
            if i.range_start > i.range_end:
                raise UserError(_("Excelsa: Range start do not bigger the range ended."))
            
    @api.constrains('range_end')
    def _check_range_end(self):
        for i in self:
            if i.range_end < i.range_start:
                raise UserError(_("Excelsa Standard: Range end do not bigger the range started."))
            if i.range_start > 100:
                raise UserError(_("Excelsa Standard: Range end do  not bigger 100."))

        