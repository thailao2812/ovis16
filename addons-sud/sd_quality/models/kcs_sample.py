# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from datetime import datetime
from odoo.tools import float_round

class KCSSample(models.Model):
    _name = 'kcs.sample'
    _inherit = ['mail.thread']

    name = fields.Char("Name",readonly=True, default='/' ,states={'draft': [('readonly', False)]})
    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    product_id = fields.Many2one("product.product", string="Product", required=True)
    categ_id = fields.Many2one(related="product_id.categ_id", store = True, string="Category",domain=[('parent_id','!=',False)])
    
    criterions_id = fields.Many2one('kcs.criterions',string="KCS Criterion",readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection(selection=[('draft', 'Draft'),('approved', 'Approved'),('reject', 'Reject')],
                            string='Status', readonly=True, copy=False, index=True, default='draft')
    
    sample_weight = fields.Float(string="Sample Weight", default=0.0000, digits=(12, 2),)
    bb_sample_weight = fields.Float(string="BB Sample Weight", default=0.0000, digits=(12, 2))
    
    picking_ids = fields.Many2many('stock.picking','stock_picking_kcs_sample_rel','kcs_sample_id','picking_id', string="GRN")
    
    date_kcs = fields.Date(string='Date', default=datetime.now().date())
    #Kiet ngay 03/01/2023
    bag_no = fields.Float(string="Bag nos.",digits=(12, 0))
    x_inspectator = fields.Many2one('x_inspectors.kcs', string='Inspectors')
    test_sample = fields.Char(string="Test Sample")

    reject_mc = fields.Boolean(string="Reject mc", tracking=True)
    
    
    
    @api.model
    def create(self,vals):
        if vals.get('name','/')=='/':
            vals['name'] = self.env['ir.sequence'].next_by_code('kcs.sample') or '/'
        return super(KCSSample, self).create(vals)

    @api.onchange('picking_ids')
    def onchange_picking(self):
        for record in self:
            criterion_id  = 0
            lst_warehouse = []
            if record.picking_ids:
                for grn in record.picking_ids:
                    lst_warehouse.append(grn.warehouse_id.id)
        return {
            'domain': {
                'criterions_id': [  ('warehouse_id','in', lst_warehouse), 
                                    ('state', 'not in', ('cancel','draft'))]
            }
        }
                
    @api.onchange("product_id")
    def onchange_product_id(self):
        self.criterions_id = False
        

    @api.depends('mc_degree')
    def _percent_mc(self):
        for this in self:
            if this.mc_degree > 0:
                this.mc = (this.mc_degree / (1 + this.mc_degree / 100)) 
            else:
                this.mc = 0.0
            return this.mc
    
    #Kiet old
    # @api.depends('mc_degree', 'sample_weight','criterions_id')
    # def _mc_deduct(self):
    #     for this in self:
    #         deduct = 0
    #         if this.mc_degree != 0:
    #             if this.criterions_id and this.criterions_id.degree_mc and this.criterions_id.degree_mc!=0:
    #                 deduct = this.mc_degree > this.criterions_id.degree_mc and (this.mc_degree - this.criterions_id.degree_mc) *(-1) or 0.0
    #             else:
    #                 degree = self.env['degree.mc'].search([('mconkett', '=', this.mc_degree)], limit=1)
    #                 deduct= degree.deduction * -1
    #             this.mc_deduct = deduct
    #         else:
    #             this.mc_deduct = 0.0
    #         return this.mc_deduct
        
        
    @api.depends('mc_degree', 'sample_weight','criterions_id')
    def _mc_deduct(self):
        for this in self:
            deduct = 0
            if this.mc_degree != 0:
                # if this.x_warehouse_id.id in [x.id for x in this.criterions_id.x_warehouse_id] and this.criterions_id.product_id.default_code in ('S16-ST', 'S18-ST'):
                    #Kiệt bổ sung thêm điều kiện Reject 
                if this.criterions_id.mc_line and this.criterions_id.reject_rule:
                    max_degree = max(this.criterions_id.mc_line.mapped('name'))
                    if this.mc_degree > max_degree and this.criterions_id.reject_rule:
                        this.reject_mc = True
                    else:
                        this.reject_mc = False
                        
                if this.criterions_id.mc_line:
                    #01/03/2024 Kiệt điều chỉnh rule + cho trường hợp độ ẩm < 14.07
                    mc_line_add = this.criterions_id.mc_line.filtered(lambda x: x.rule == 'addition')
                    mc_line_add = mc_line_add and mc_line_add[0] or False
                    if mc_line_add and round(this.mc_degree,2) <= mc_line_add.name:
                        deduct = (mc_line_add.name - round(this.mc_degree,2)) * (mc_line_add.percent /100)
                    else:
                        for x in this.criterions_id.mc_line:
                            if round(this.mc_degree,2) == x.name:
                                deduct = - x.percent
                                
                elif this.criterions_id and this.criterions_id.degree_mc and this.criterions_id.degree_mc!=0:
                    deduct = this.mc_degree > this.criterions_id.degree_mc and (this.mc_degree - this.criterions_id.degree_mc) *(-1) or 0.0
                else:
                    degree = self.env['degree.mc'].search([('mconkett', '=', this.mc_degree)], limit=1)
                    deduct= degree.deduction * -1
                this.mc_deduct = deduct
                
            else:
                this.mc_deduct = 0.0
            return this.mc_deduct
        
            
#     @api.depends('mc_degree', 'sample_weight')
#     def _mc_deduct(self):
#         for this in self:
#             if this.mc_degree != 0:
#                 degree = self.env['degree.mc'].search([('mconkett', '=', this.mc_degree)], limit=1)
# #                 if not degree:
# #                     raise UserError(_('You much Define Degree mc'))
#                 this.mc_deduct = degree.deduction * -1
#                 this.mc_deduct = this.mc_deduct 
#             else:
#                 this.mc_deduct = 0.0
#             return this.mc_deduct
    
    @api.depends('sample_weight','fm_gram')
    def _percent_fm(self):
        for this in self:
            if this.sample_weight != 0:
                this.fm = (this.fm_gram / this.sample_weight or 0.0000)*100
            else:
                this.fm = 0.0
            return this.fm

    @api.depends('fm','criterions_id')
    def _fm_deduct(self):
        for this in self:
            if this.fm > 0 and this.criterions_id:
                fm_deduct = deduct = percent_fm = 0.0000
                percent_fm = this.fm
                
                # if this.criterions_id.foreign_matter_ids and this.criterions_id.reject_rule:
                #     max_degree = max(this.criterions_id.foreign_matter_ids.mapped('range_end')) 
                #     if percent_fm > max_degree:
                #         this.reject_foreign = True
                #     else: 
                #         this.reject_foreign = False
                # else: 
                #     this.reject_foreign = False
                    
                if this.criterions_id.finished_products:
                    self.env.cr.execute('''SELECT id FROM foreign_matter WHERE criterion_id = %s ORDER BY range_end desc'''%(this.criterions_id.id))
                    for fm_standard in self.env.cr.dictfetchall(): 
                        deduct =0.0
                        fm_obj = self.env['foreign.matter'].browse(fm_standard['id'])
                        percent = fm_obj.percent or 0.0
                        if fm_obj.range_start <= percent_fm and  percent_fm <= fm_obj.range_end:
                            deduct = (percent_fm - fm_obj.range_start) * (percent/100)
                            percent_fm = fm_obj.range_start
                        fm_deduct += deduct
                    this.fm_deduct = fm_deduct *(-1)
                else:
                    addition = 0
                    if percent_fm >=1:
                        self.env.cr.execute('''SELECT id FROM foreign_matter WHERE criterion_id = %s AND range_start >= 1 ORDER BY range_end desc'''%(this.criterions_id.id))
                        for fm_standard in self.env.cr.dictfetchall(): 
                            deduct =0.0
                            fm_obj = self.env['foreign.matter'].browse(fm_standard['id'])
                            percent = fm_obj.percent or 0.0
                            if fm_obj.range_start <= percent_fm and  percent_fm <= fm_obj.range_end:
                                deduct = (percent_fm - fm_obj.range_start) * (percent/100)
                                percent_fm = fm_obj.range_start
                            fm_deduct += deduct
                        this.fm_deduct = fm_deduct *(-1)
                    else:
                        # self.env.cr.execute('''SELECT id FROM foreign_matter WHERE criterion_id = %s AND range_start <= 0.9 ORDER BY range_end desc'''%(this.criterions_id.id))
                        # for fm_standard in self.env.cr.dictfetchall(): 
                        #     deduct =0.0
                        #     fm_obj = self.env['foreign.matter'].browse(fm_standard['id'])
                        #     percent = fm_obj.percent or 0.0
                        #     if fm_obj.range_start <= percent_fm and  percent_fm < fm_obj.range_end:
                        #         deduct = (0.9 - percent_fm) * (percent/100)
                        #         percent_fm = fm_obj.range_start
                        #     fm_deduct += deduct
                        # this.fm_deduct = fm_deduct
                        #Kiệt + range
                        fm_obj = self.env['foreign.matter'].search([('criterion_id','=',this.criterions_id.id),('rule','=','addition')], limit = 1)
                        if fm_obj:
                            deduct =0.0
                            percent = fm_obj.percent or 0.0
                            if fm_obj.range_start <= percent_fm and  percent_fm < fm_obj.range_end:
                                addition = (fm_obj.range_end - percent_fm) * fm_obj.percent /100
                            this.fm_deduct = addition 
            else:
                this.fm_deduct = 0.0

            return this.fm_deduct
            
    # @api.depends('fm','criterions_id')
    # def _fm_deduct(self):
    #     for this in self:
    #         if this.fm > 0 and this.criterions_id:
    #             fm_deduct = deduct = percent_fm = 0.0000
    #             percent_fm = this.fm
                
    #             if percent_fm >=1:
    #                 self.env.cr.execute('''SELECT id FROM foreign_matter WHERE criterion_id = %s AND range_start >= 1 ORDER BY range_end desc'''%(this.criterions_id.id))
    #                 for fm_standard in self.env.cr.dictfetchall(): 
    #                     deduct =0.0
    #                     fm_obj = self.env['foreign.matter'].browse(fm_standard['id'])
    #                     percent = fm_obj.percent or 0.0
    #                     if fm_obj.range_start <= percent_fm and  percent_fm <= fm_obj.range_end:
    #                         deduct = (percent_fm - fm_obj.range_start) * (percent/100)
    #                         percent_fm = fm_obj.range_start
    #                     fm_deduct += deduct
    #                 this.fm_deduct = fm_deduct *(-1)
    #             else:
    #                 self.env.cr.execute('''SELECT id FROM foreign_matter WHERE criterion_id = %s AND range_start <= 0.9 ORDER BY range_end desc'''%(this.criterions_id.id))
    #                 for fm_standard in self.env.cr.dictfetchall(): 
    #                     deduct =0.0
    #                     fm_obj = self.env['foreign.matter'].browse(fm_standard['id'])
    #                     percent = fm_obj.percent or 0.0
    #                     if fm_obj.range_start <= percent_fm and  percent_fm < fm_obj.range_end:
    #                         deduct = (0.9 - percent_fm) * (percent/100)
    #                         percent_fm = fm_obj.range_start
    #                     fm_deduct += deduct
    #                 this.fm_deduct = fm_deduct
    #         else:
    #             this.fm_deduct = 0.0
    #         return this.fm_deduct
            
    @api.depends('bb_sample_weight','black_gram')
    def _percent_black(self):
        for this in self:
            if this.bb_sample_weight > 0 and this.black_gram > 0:
                black = this.black_gram / this.bb_sample_weight or 0.0000
                this.black = black * 100
            else:
                this.black = 0.0
            return this.black
            
    @api.depends('bb_sample_weight','broken_gram')
    def _percent_broken(self):
        for this in self:
            if this.bb_sample_weight > 0 and this.broken_gram > 0:
                broken = this.broken_gram / this.bb_sample_weight or 0.0000
                this.broken = broken * 100
            else:
                this.broken = 0.0
            return this.broken
    
    # @api.depends('black','broken','brown','criterions_id')
    # def _broken_deduct(self):
    #     for this in self:
    #         if this.black > 0 and this.broken > 0 and this.criterions_id:
    #             broken_deduct = deduct = percent_bb = 0.0000
    #             percent_bb = this.black + this.broken 
    #
    #             self.env.cr.execute('''SELECT id FROM Broken_Standard WHERE criterion_id = %s ORDER BY range_end desc'''%(this.criterions_id.id))
    #             for broken_standard in self.env.cr.dictfetchall(): 
    #                 deduct =0.0
    #                 broken_obj = self.env['broken.standard'].browse(broken_standard['id'])
    #                 percent = broken_obj.percent or 0.0
    #                 if broken_obj.range_start <= percent_bb and  percent_bb <= broken_obj.range_end:
    #                     deduct = (percent_bb - broken_obj.range_start) * (percent/100)
    #                     percent_bb = broken_obj.range_start
    #                 broken_deduct += deduct
    #             this.broken_deduct = broken_deduct *(-1) 
    #         else:
    #             this.broken_deduct = 0.0
    #         return this.broken_deduct
    
    #Kiệt 24/11 điều chỉnh chỉnh rule + cho mùa vụ mới
    @api.depends('black','broken','brown','criterions_id')
    def _broken_deduct(self):
        for this in self:
            if this.black > 0 and this.broken > 0 and this.criterions_id:
                broken_deduct = deduct = percent_bb = 0.0000
                percent_bb = this.black + this.broken 
                
                # if this.criterions_id.broken_standard_ids and this.criterions_id.reject_rule:
                #     max_degree = max(this.criterions_id.broken_standard_ids.mapped('range_end')) 
                #     if percent_bb > max_degree:
                #         this.reject_bb = True
                #     else:
                #         this.reject_bb = False
                
                #Kiệt 24/11 điều chỉnh chỉnh rule - cho mùa vụ mới
                if percent_bb >=3:      
                    self.env.cr.execute('''SELECT id FROM Broken_Standard WHERE criterion_id = %s and rule ='subtraction' ORDER BY range_end desc'''%(this.criterions_id.id))
                    for broken_standard in self.env.cr.dictfetchall(): 
                        deduct =0.0
                        broken_obj = self.env['broken.standard'].browse(broken_standard['id'])
                        percent = broken_obj.percent or 0.0
                        if broken_obj.range_start <= percent_bb and  percent_bb <= broken_obj.range_end:
                            deduct = (percent_bb - broken_obj.range_start) * (percent/100)
                            percent_bb = broken_obj.range_start
                        broken_deduct += deduct
                    this.broken_deduct = broken_deduct *(-1) 
                
                #Kiệt 24/11 điều chỉnh chỉnh rule + cho mùa vụ mới
                elif percent_bb <3 and this.brown <6:   
                    self.env.cr.execute('''SELECT id FROM Broken_Standard WHERE criterion_id = %s and rule ='addition' ORDER BY range_end desc limit 1'''%(this.criterions_id.id))
                    for broken_standard in self.env.cr.dictfetchall(): 
                        deduct =0.0
                        broken_obj = self.env['broken.standard'].browse(broken_standard['id'])
                        percent = broken_obj.percent or 0.0
                        if percent_bb <= broken_obj.range_end:
                            addition = (broken_obj.range_end - percent_bb) * (percent/100)
                            this.broken_deduct = addition
                
                elif percent_bb <3 and this.brown >6: 
                    this.broken_deduct = 0
                    
            else:
                this.broken_deduct = 0.0
            return this.broken_deduct
            
    @api.depends('bb_sample_weight','brown_gram')
    def _percent_brown(self):
        for this in self:
            if this.bb_sample_weight != 0:
                brown = this.brown_gram / this.bb_sample_weight  or  0.0000
                this.brown = brown * 100
            else:
                this.brown = 0.0
            return this.brown
    
    @api.depends('brown','criterions_id','broken','black')
    def _brown_deduct(self):
        for this in self:
            if this.criterions_id.finished_products:
                if this.brown > 0 and this.criterions_id:
                    brown_deduct = deduct = percent_brown = 0.000
                    percent_brown = this.brown
                    
                    self.env.cr.execute('''SELECT id FROM brown_standard WHERE criterion_id = %s ORDER BY range_end DESC'''%(self.criterions_id.id))
                    for brown_standard in self.env.cr.dictfetchall(): 
                        deduct =0.0
                        brown_obj = self.env['brown.standard'].browse(brown_standard['id'])
                        percent = brown_obj.percent or 0.0
                            
                        if brown_obj.range_start <= percent_brown and percent_brown <= brown_obj.range_end:
                            deduct = (percent_brown - brown_obj.range_start) * (percent/100)
                            percent_brown = brown_obj.range_start
                        brown_deduct += deduct

                    this.brown_deduct = brown_deduct *(-1) 
            else:
                if (this.broken + this.black) < 5 and (this.broken + this.black + this.brown)  <= 11 and this.criterions_id:
                    this.brown_deduct = 0.0
                    return
                if this.brown > 0 and this.criterions_id:
                    brown_deduct = deduct = percent_brown = 0.000
                    percent_brown = this.brown
                    
                    self.env.cr.execute('''SELECT id FROM brown_standard WHERE criterion_id = %s ORDER BY range_end DESC'''%(self.criterions_id.id))
                    for brown_standard in self.env.cr.dictfetchall(): 
                        deduct =0.0
                        brown_obj = self.env['brown.standard'].browse(brown_standard['id'])
                        percent = brown_obj.percent or 0.0
                            
                        if brown_obj.range_start <= percent_brown and percent_brown <= brown_obj.range_end:
                            deduct = (percent_brown - brown_obj.range_start) * (percent/100)
                            percent_brown = brown_obj.range_start
                        brown_deduct += deduct
                        
                    this.brown_deduct = brown_deduct *(-1) 
                else:
                    this.brown_deduct = 0.0
            return this.brown_deduct
    #Old Kiet    
    # @api.depends('brown','criterions_id','broken','black')
    # def _brown_deduct(self):
    #     for this in self:
    #         if (this.broken + this.black) < 5 and (this.broken + this.black + this.brown)  <= 11 and this.criterions_id:
    #             this.brown_deduct = 0.0
    #             return
    #         if this.brown > 0 and this.criterions_id:
    #             brown_deduct = deduct = percent_brown = 0.000
    #             percent_brown = this.brown
    #
    #             self.env.cr.execute('''SELECT id FROM brown_standard WHERE criterion_id = %s ORDER BY range_end DESC'''%(self.criterions_id.id))
    #             for brown_standard in self.env.cr.dictfetchall(): 
    #                 deduct =0.0
    #                 brown_obj = self.env['brown.standard'].browse(brown_standard['id'])
    #                 percent = brown_obj.percent or 0.0
    #
    #                 if brown_obj.range_start <= percent_brown and percent_brown <= brown_obj.range_end:
    #                     deduct = (percent_brown - brown_obj.range_start) * (percent/100)
    #                     percent_brown = brown_obj.range_start
    #                 brown_deduct += deduct
    #
    #             this.brown_deduct = brown_deduct *(-1) 
    #         else:
    #             this.brown_deduct = 0.0
    #         return this.brown_deduct
            
    @api.depends('sample_weight','mold_gram')
    def _percent_mold(self):
        for this in self:
            if this.sample_weight != 0:
                mold = this.mold_gram / this.sample_weight  or 0.0000
                this.mold = mold * 100
            else:
                this.mold = 0.0
            return this.mold
            
    @api.depends('mold','criterions_id')
    def _mold_deduct(self):
        for this in self:
            if this.mold and this.criterions_id:
                mold_deduct = 0.0000
                percent_brown = this.mold
                
                self.env.cr.execute('''SELECT id FROM mold_standard WHERE criterion_id = %s ORDER BY range_end DESC'''%(this.criterions_id.id))
                for mold_standard in self.env.cr.dictfetchall():
                    mold_obj = self.env['mold.standard'].browse(mold_standard['id'])
                    deduct =0.0
                        
                    if mold_obj.range_start <= percent_brown and percent_brown <= mold_obj.range_end:
                        deduct = (percent_brown - mold_obj.range_start) * (mold_obj.percent/100 or 0.0)
                        percent_brown = mold_obj.range_start
                    mold_deduct += deduct
                this.mold_deduct = mold_deduct *(-1)
            else:
                this.mold_deduct = 0.0
            return this.mold_deduct
    
    @api.depends('sample_weight','cherry_gram')
    def _percent_cherry(self):
        for this in self:
            if this.sample_weight > 0 and this.cherry_gram > 0:
                cherry = this.cherry_gram / this.sample_weight  or 0.0000
                this.cherry = cherry * 100
            else:
                this.cherry = 0.0
            return this.cherry
            
    @api.depends('sample_weight','excelsa_gram')
    def _percent_excelsa(self):
        for this in self:
            if this.sample_weight > 0 and this.excelsa_gram > 0:
                excelsa = this.excelsa_gram / this.sample_weight  or 0.0000
                this.excelsa = excelsa * 100
            else:
                this.excelsa = 0.0
            return this.excelsa
            
    @api.depends('excelsa','criterions_id')
    def _excelsa_deduct(self):
        for this in self:
            if this.excelsa and this.criterions_id:
                excelsa_deduct = 0.0000
                percent_brown = this.excelsa
                
                self.env.cr.execute('''SELECT id FROM excelsa_standard WHERE criterion_id = %s ORDER BY range_end DESC'''%(this.criterions_id.id))
                for excelsa_standard in self.env.cr.dictfetchall():
                    excelsa_obj = self.env['excelsa.standard'].browse(excelsa_standard['id'])
                    deduct =0.0
                        
                    if excelsa_obj.range_start <= percent_brown and percent_brown <= excelsa_obj.range_end:
                        deduct = (percent_brown - excelsa_obj.range_start) * (excelsa_obj.percent/100 or 0.0)
                        percent_brown = excelsa_obj.range_start
                    excelsa_deduct += deduct
                this.excelsa_deduct = excelsa_deduct *(-1)
            else:
                this.excelsa_deduct = 0.0
            return this.excelsa_deduct

    @api.depends('sample_weight','screen20_gram')
    def _percent_screen20(self):
        for this in self:
            if this.sample_weight != 0:
                screen20 = this.screen20_gram / this.sample_weight or 0.0000
                this.screen20 = screen20 * 100
            else:
                this.screen20 = 0.0
            return this.screen20

    @api.depends('sample_weight','screen19_gram')
    def _percent_screen19(self):
        for this in self:
            if this.sample_weight != 0:
                screen19 = this.screen19_gram / this.sample_weight or 0.0000
                this.screen19 = screen19 * 100
            else:
                this.screen19 = 0.0
            return this.screen19
            
    @api.depends('sample_weight','screen18_gram')
    def _percent_screen18(self):
        for this in self:
            if this.sample_weight != 0:
                screen18 = this.screen18_gram / this.sample_weight or 0.0000
                this.screen18 = screen18 * 100
            else:
                this.screen18 = 0.0
            return this.screen18
    
    @api.depends('screen20','screen19','screen18','screen16','criterions_id')
    def _screen18_deduct(self):
        for this in self:
            if this.screen18 > 0 and this.criterions_id:
                oversc18 = percent_oversc = standard = percent = 0.0000
    
                percent_oversc = this.screen18
                standard = this.criterions_id.standard_screen18
                percent = this.criterions_id.percent_screen18
                if percent_oversc <= standard:
                    oversc18 = (standard - percent_oversc) * percent /100
                
                if this.screen16 + this.screen18 + this.screen19 + this.screen20 >= 45:
                    this.oversc18 = 0
                else:
                    this.oversc18  = float_round(oversc18 * (-1), precision_rounding=0.01, rounding_method='UP')
            else:
                this.oversc18 = 0
            return this.oversc18

    @api.depends('sample_weight', 'screen17_gram')
    def _percent_screen17(self):
        for this in self:
            if this.sample_weight != 0:
                screen17 = this.screen17_gram / this.sample_weight or 0.0000
                this.screen17 = screen17 * 100
            else:
                this.screen17 = 0.0
            return this.screen17

    @api.depends('sample_weight','screen16_gram')
    def _percent_screen16(self):
        for this in self:
            if this.sample_weight != 0:
                screen16 = this.screen16_gram / this.sample_weight  or 0.0000
                this.screen16 = screen16 * 100
            else:
                this.screen16 = 0.0
            return this.screen16

    @api.depends('sample_weight', 'screen15_gram')
    def _percent_screen15(self):
        for this in self:
            if this.sample_weight != 0:
                screen15 = this.screen15_gram / this.sample_weight or 0.0000
                this.screen15 = screen15 * 100
            else:
                this.screen15 = 0.0
            return this.screen15

    @api.depends('sample_weight', 'screen14_gram')
    def _percent_screen14(self):
        for this in self:
            if this.sample_weight != 0:
                screen14 = this.screen14_gram / this.sample_weight or 0.0000
                this.screen14 = screen14 * 100
            else:
                this.screen14 = 0.0
            return this.screen14
            
    @api.depends('screen16', 'screen18','screen17','screen19','screen20','criterions_id')
    def _screen16_deduct(self):
        for this in self:
            if this.screen16 > 0 and this.criterions_id:
                oversc16 = percent_oversc = standard = percent = 0.0000
    
                percent_oversc = this.screen16
                standard = this.criterions_id.standard_screen18_16
                percent = this.criterions_id.percent_screen18_16
                if 0 < percent_oversc and  percent_oversc < standard:
                    oversc16 = (standard - percent_oversc) * (percent/100 or 0.0)
                
                if this.screen16 + this.screen17 + this.screen18 + this.screen19 + this.screen20 < 40:
                    oversc16 = (standard - percent_oversc) * (percent/100 or 0.0)
                    this.oversc16 = oversc16 * (-1) 
                else:
                    this.oversc16 = 0
            else:
                this.oversc16 = 0
            return this.oversc16
            
    @api.depends('sample_weight','screen13_gram')
    def _percent_screen13(self):
        for this in self:
            if this.sample_weight > 0 and this.screen13_gram > 0:
                screen13 = this.screen13_gram / this.sample_weight or 0.0000
                this.screen13 = screen13 * 100
            else:
                this.screen13 = 0.0
            return this.screen13
            
    @api.depends('screen13', 'screen14', 'screen15','screen16', 'screen17', 'screen18', 'screen19', 'screen20','criterions_id')
    def _screen13_deduct(self):
        for this in self:
            if this.criterions_id.finished_products:
                if this.screen13 > 0 and this.criterions_id:
                    oversc13 = percent_oversc = standard = percent = 0.0000
                    
                    percent_oversc =  this.screen13 +  this.screen14 +  this.screen15 + this.screen16 + this.screen17 + this.screen18 + this.screen19 + this.screen20
                    standard = this.criterions_id.standard_screen13
                    percent = this.criterions_id.percent_screen13
                    
                    if percent_oversc < standard:
                        oversc13 = (standard - percent_oversc) * percent /100
                        this.oversc13 = oversc13 * (-1) 
                else:
                    this.oversc13 = 0
            else:
                if this.screen13 > 0 and this.criterions_id:
                    oversc13 = percent_oversc = standard = percent = 0.0000
                    
                    percent_oversc = this.screen13
                    standard = this.criterions_id.standard_screen13
                    percent = this.criterions_id.percent_screen13
                    
                    if percent_oversc < standard:
                        oversc13 = (standard - percent_oversc) * (percent/100 or 0.0)
                    if this.screen13 + this.screen14 + this.screen15 + this.screen16 + this.screen17 + this.screen18 + this.screen19 + this.screen20 < 90:
                        oversc13 = (standard - (this.screen16 + this.screen17 + this.screen18 + this.screen19 + this.screen20 + this.screen13 + this.screen14 + this.screen15)) * (percent/100 or 0.0)
                        this.oversc13 = oversc13 * (-1) 
                    else:
                        this.oversc13 = 0
            return this.oversc13
            
    @api.depends('sample_weight','screen19_gram','screen20_gram','screen18_gram','screen16_gram','screen13_gram','belowsc12_gram')
    def _greatersc12_gram(self):
        for this in self:
            if this.sample_weight > 0 and (this.screen20_gram + this.screen19_gram + this.screen18_gram + this.screen16_gram + this.screen13_gram + this.belowsc12_gram) < this.sample_weight:
                this.greatersc12_gram = this.sample_weight - (this.screen20_gram + this.screen19_gram + this.screen18_gram + this.screen16_gram + this.screen13_gram + this.belowsc12_gram)
            else:
                this.greatersc12_gram = 0.0
                
            if this.sample_weight > 0 and (this.screen20_gram + this.screen19_gram + this.screen18_gram + this.screen16_gram + this.screen13_gram) == 0:
                this.greatersc12_gram = 0.0
            return this.greatersc12_gram

    @api.depends('sample_weight','greatersc12_gram')
    def _percent_greatersc12(self):
        for this in self:
            if this.sample_weight > 0 and this.greatersc12_gram > 0:
                greatersc12 = this.greatersc12_gram / this.sample_weight or 0.0000
                this.greatersc12 = greatersc12 * 100
            else:
                this.greatersc12 = 0.0
            return this.greatersc12

    @api.depends('sample_weight','belowsc12_gram')
    def _percent_belowsc12(self):
        for this in self:
            if this.sample_weight > 0 and this.belowsc12_gram > 0:
                belowsc12 = this.belowsc12_gram / this.sample_weight or 0.0000
                this.belowsc12 = belowsc12 * 100
            else:
                this.belowsc12 = 0.0
                
    @api.depends('belowsc12','criterions_id')
    def _screen12_deduct(self):
        for this in self:
            if this.belowsc12 and this.criterions_id:
                sc12_deduct = 0.0000
                percent_brown = this.belowsc12
                
                self.env.cr.execute('''SELECT id FROM over_screen12 WHERE criterion_id = %s ORDER BY range_end DESC'''%(this.criterions_id.id))
                for sc12_standard in self.env.cr.dictfetchall():
                    sc12_obj = self.env['over.screen12'].browse(sc12_standard['id'])
                    deduct =0.0
                        
                    if sc12_obj.range_start <= percent_brown and percent_brown <= sc12_obj.range_end:
                        deduct = (percent_brown - sc12_obj.range_start) * (sc12_obj.percent/100 or 0.0)
                        percent_brown = sc12_obj.range_start
                    sc12_deduct += deduct
                this.oversc12 = sc12_deduct *(-1)
            else:
                this.oversc12 = 0.0
            return this.oversc12
    
    @api.depends('sample_weight','burned_gram')
    def _percent_burned(self):
        for this in self:
            if this.sample_weight > 0 and this.burned_gram > 0:
                burned = this.burned_gram / this.sample_weight or 0.0000
                this.burned = burned * 100
            else:
                this.burned = 0.0
            return this.burned
            
    @api.depends('burned','burned_gram','sample_weight')
    def _burned_deduct(self):
        for this in self:
            if this.burned > 0 and this.criterions_id:
                burned_deduct = percent_burned = standard = percent = 0.0000
                
                percent_burned = this.burned 
                standard = this.criterions_id.standard_burned
                percent = this.criterions_id.percent_burned
                
                if standard > 0 and percent_burned > standard:
                    burned_deduct = (percent_burned - standard) * percent/100
                this.burned_deduct = burned_deduct * (-1) 
            else:
                this.burned_deduct = 0.0
            return this.burned_deduct
            
    @api.depends('sample_weight','eaten_gram')
    def _percent_eaten(self):
        for this in self:
            if this.bb_sample_weight > 0 and this.eaten_gram > 0:
                eaten = this.eaten_gram / this.bb_sample_weight or 0.0000
                this.eaten = eaten * 100
            else:
                this.eaten = 0.0
            return this.eaten
    
# SON: insect_bean và eaten_bean là cùng 1 loại, insect_bean mới tạo sau theo quy trình mới. Nhưng toàn bộ các form mang chất lượng
# đều đang lấy giá trị của eaten_bean => Lấy eaten_bean để tính cho insect_bean_deduct để ko tạo thêm field compute.
    @api.depends('eaten','criterions_id')
    def _insect_bean_deduct(self):
        for this in self:
            
            if this.eaten > 0 and this.criterions_id:
                insect_bean_deduct = insect_obj = percent_insect_bean = 0.0000
                percent_insect_bean = this.eaten
                
                if percent_insect_bean >=1:
                    self.env.cr.execute('''SELECT id FROM insect_bean WHERE criterion_id = %s AND range_start >= 1 ORDER BY range_end desc'''%(this.criterions_id.id))
                    for fm_standard in self.env.cr.dictfetchall(): 
                        deduct =0.0
                        insect_obj = self.env['insect.bean'].browse(fm_standard['id'])
                        percent = insect_obj.percent or 0.0
                        if insect_obj.range_start <= percent_insect_bean and  percent_insect_bean <= insect_obj.range_end:
                            deduct = (percent_insect_bean - insect_obj.range_start) * (percent/100)
                            percent_insect_bean = insect_obj.range_start
                        insect_bean_deduct += deduct
                    this.insect_bean_deduct = insect_bean_deduct *(-1)
                    
                else:
                    self.env.cr.execute('''SELECT id FROM insect_bean WHERE criterion_id = %s AND range_start <= 0.9 ORDER BY range_end desc'''%(this.criterions_id.id))
                    for fm_standard in self.env.cr.dictfetchall(): 
                        deduct =0.0
                        insect_obj = self.env['insect.bean'].browse(fm_standard['id'])
                        percent = insect_obj.percent or 0.0
                        if insect_obj.range_start <= percent_insect_bean and  percent_insect_bean < insect_obj.range_end:
                            deduct = (1 - percent_insect_bean) * (percent/100)
                            percent_insect_bean = insect_obj.range_start
                        insect_bean_deduct += deduct
                    this.insect_bean_deduct = insect_bean_deduct
            else:
                this.insect_bean_deduct = 0.0
            return this.insect_bean_deduct
            
    @api.depends('sample_weight','insect_bean_gram')
    def _insect_bean(self):
        for this in self:
            if this.sample_weight != 0:
                insect_bean_gram = this.insect_bean_gram / this.sample_weight  or 0.0000
                this.insect_bean = insect_bean_gram * 100
            else:
                this.insect_bean = 0.0
            return this.insect_bean
                
    @api.depends('sample_weight','immature_gram')
    def _percent_immature(self):
        for this in self:
            if this.bb_sample_weight != 0:
                immature = this.immature_gram / this.bb_sample_weight  or 0.0000
                this.immature = immature * 100
                return this.immature
            
    @api.depends('sample_weight','bb12_gram')
    def _percent_bb12(self):
        for this in self:
            if this.sample_weight != 0:
                bb12 = this.bb12_gram / this.sample_weight or 0.0000
                this.bb12 = bb12 * 100
            else:
                this.bb12 = 0.0
            return this.bb12
    
    @api.depends('sample_weight','bb_sample_weight','mc_deduct','fm_deduct','broken_deduct','brown_deduct'
                ,'mold_deduct','excelsa_deduct','oversc16','oversc13','burned_deduct','oversc12','oversc18','insect_bean_deduct')
    def _compute_deduction(self):   
        for line in self:
            deduction = (line.mc_deduct + line.fm_deduct + line.broken_deduct +
                    line.brown_deduct + line.mold_deduct + line.excelsa_deduct + line.insect_bean_deduct +
                    line.oversc13 + line.oversc16 + line.burned_deduct  + line.oversc18 + line.oversc12) or 0.0
            line.deduction = deduction
            return line.deduction
    
    @api.depends('broken','black','brown','criterions_id')
    def _bbb_deduct(self):
        for this in self:
            if (this.broken + this.black) < 5 and (this.broken + this.black + this.brown)  <= 11 and this.criterions_id:
                this.bbb =0
            else:
                this.bbb = this.broken_deduct + this.brown_deduct
    
    # @api.depends('sample_weight','insect_bean_gram')
    # def _insect_bean(self):
    #     for this in self:
    #         if this.sample_weight != 0:
    #             insect_bean_gram = this.insect_bean_gram / this.sample_weight  or 0.0000
    #             this.insect_bean = insect_bean_gram * 100
    #         else:
    #             this.insect_bean = 0.0
                
    mc_degree = fields.Float(string="MCDegree", default=0.0000, digits=(12, 2), )
    mc = fields.Float(compute='_percent_mc', string="MC_%", readonly=True, store=True, default=0.0000, digits=(12, 2))
    mc_deduct = fields.Float(compute='_mc_deduct', string="MC Deduct", readonly=True, store=True, default=0.0000, digits=(12, 2))
    
    fm_gram = fields.Float(string="FM Gram", default=0.0000, digits=(12, 2), )
    fm = fields.Float(compute='_percent_fm',string="FM_%", readonly=True, store=True, default=0.0000, digits=(12, 2),group_operator="avg")
    fm_deduct = fields.Float(compute='_fm_deduct', string="FM Deduct", readonly=True, store=True, default=0.0000, digits=(12, 2))
    
    black_gram = fields.Float(string="Black Gram", default=0.0000, digits=(12, 2), )
    black = fields.Float(compute='_percent_black',group_operator="avg",string="Black_%", readonly=True, store=True, default=0.0000, digits=(12, 2))
    
    broken_gram = fields.Float(string="Broken Gram", default=0.0000, digits=(12, 2), )
    broken = fields.Float(compute='_percent_broken',group_operator="avg",string="Broken_%", readonly=True, store=True, default=0.0000, digits=(12, 2))
    broken_deduct = fields.Float(compute='_broken_deduct', string="BB Deduct", readonly=True, store=True, default=0.0000, digits=(12, 2))
    
    brown_gram = fields.Float(string="Brown Gram", default=0.0000, digits=(12, 2), ) 
    brown = fields.Float(compute='_percent_brown',group_operator="avg",string="Brown_%", readonly=True, store=True, default=0.0000, digits=(12, 2))
    brown_deduct = fields.Float(compute='_brown_deduct',string="Brown Deduct", readonly=True, store=True, default=0.0000, digits=(12, 2))
    
    bbb = fields.Float(compute='_bbb_deduct',string="BBB", readonly=True, store=True, default=0.0000, digits=(12, 2))
    
    mold_gram = fields.Float(string="Mold Gram", default=0.0000, digits=(12, 2), )
    mold = fields.Float(compute='_percent_mold',group_operator="avg",string="Mold_%", readonly=True, store=True, default=0.0000, digits=(12, 2))
    mold_deduct = fields.Float(compute='_mold_deduct',string="Mold Deduct", readonly=True, store=True, default=0.0000, digits=(12, 2))
    
    
    insect_bean_gram = fields.Float(string="Insect bean Gram", default=0.0000, digits=(12, 2), )
    insect_bean = fields.Float(compute='_insect_bean',group_operator="avg",string="Insect bean_%", readonly=True, store=True, default=0.0000, digits=(12, 2))
# Lấy insect_bean_deduct đc tính từ eaten, eaten_gram.
    insect_bean_deduct = fields.Float(compute='_insect_bean_deduct',string="Eaten bean Deduct", readonly=True, store=True, default=0.0000, digits=(12, 2))
    
    cherry_gram = fields.Float(string="Cherry Gram", default=0.0000, )
    cherry = fields.Float(compute='_percent_cherry', group_operator="avg",string="Cherry_%", readonly=True, store=True, default=0.0000, digits=(12, 2))
    
    excelsa_gram = fields.Float(string="Excelsa Gram", default=0.0000, digits=(12, 2), )
    excelsa = fields.Float(compute='_percent_excelsa', group_operator="avg", string="Excelsa_%", readonly=True, store=True, default=0.0000, digits=(12, 2))
    excelsa_deduct = fields.Float(compute='_excelsa_deduct' ,string="Excelsa Deduct", readonly=True, store=True, default=0.0000, digits=(12, 2))
    
    screen20_gram = fields.Float(string="Screen20 Gram", default=0.0000, digits=(12, 2), )
    screen20 = fields.Float(compute='_percent_screen20',group_operator="avg", string="Screen20_%", readonly=True, store=True, default=0.0000, digits=(12, 2))
    screen19_gram = fields.Float(string="Screen19 Gram", default=0.0000, digits=(12, 2), )
    screen19 = fields.Float(compute='_percent_screen19',group_operator="avg", string="Screen19_%", readonly=True, store=True, default=0.0000, digits=(12, 2))

    screen18_gram = fields.Float(string="Screen18 Gram", default=0.0000, digits=(12, 2), )
    screen18 = fields.Float(compute='_percent_screen18',group_operator="avg", string="Screen18_%", readonly=True, store=True, default=0.0000, digits=(12, 2))
    oversc18 = fields.Float(compute='_screen18_deduct',string="OverSc18 Deduct", readonly=True, store=True, default=0.0000, digits=(12, 2))

    screen17_gram = fields.Float(string="Screen17 Gram", default=0.0000,
                                 digits=(12, 2), )
    screen17 = fields.Float(compute='_percent_screen17', group_operator="avg",
                            string="Screen17 %", readonly=True, store=True,
                            default=0.0000, digits=(12, 2))

    screen16_gram = fields.Float(string="Screen16 Gram", default=0.0000, digits=(12, 2), )
    screen16 = fields.Float(compute='_percent_screen16',group_operator="avg", string="Screen16 %", readonly=True, store=True, default=0.0000, digits=(12, 2))
    oversc16 = fields.Float(compute='_screen16_deduct',string="OverSc16 Deduct", readonly=True, store=True, default=0.0000, digits=(12, 2))

    screen15_gram = fields.Float(string="Screen15 Gram", default=0.0000,
                                 digits=(12, 2), )
    screen15 = fields.Float(compute='_percent_screen15', group_operator="avg",
                            string="Screen15 %", readonly=True, store=True,
                            default=0.0000, digits=(12, 2))

    screen14_gram = fields.Float(string="Screen14 Gram", default=0.0000,
                                 digits=(12, 2), )
    screen14 = fields.Float(compute='_percent_screen14', group_operator="avg",
                            string="Screen14 %", readonly=True, store=True,
                            default=0.0000, digits=(12, 2))
    
    screen13_gram = fields.Float(string="Screen13 Gram", default=0.0000, digits=(12, 2), )
    screen13 = fields.Float(compute='_percent_screen13',group_operator="avg", string="Screen13_%", readonly=True, store=True, default=0.0000, digits=(12, 2))
    oversc13 = fields.Float(compute='_screen13_deduct',string="OverSc13 Deduct", readonly=True, store=True, default=0.0000, digits=(12, 2))
    
    # greatersc12_gram = fields.Float(string="Screen12 Gram", default=0.000, digits=(12, 2), )
    greatersc12_gram = fields.Float(compute='_greatersc12_gram',group_operator="avg", string="Screen12 Gram", readonly=True, store=True, default=0.000, digits=(12, 2))
    greatersc12 = fields.Float(compute='_percent_greatersc12',group_operator="avg", string="Screen12_%", readonly=True, store=True, default=0.000)

    belowsc12_gram = fields.Float(string="Belowsc12 Gram", default=0.000, digits=(12, 2), )
    belowsc12 = fields.Float(compute='_percent_belowsc12',group_operator="avg", string="Belowsc12_%", readonly=True, store=True, default=0.000)
    oversc12 = fields.Float(compute='_screen12_deduct',string="OverSc12 Deduct", readonly=True, store=True, default=0.0000, digits=(12, 2))
    
    burned_gram = fields.Float(string="Burned Gram", default=0.0000, digits=(12, 2), )
    burned = fields.Float(compute='_percent_burned',group_operator="avg", string="Burned_%", default=0.0000, digits=(12, 2),store=True)
    burned_deduct = fields.Float(compute='_burned_deduct',string="Burned Deduct",  store=True,  digits=(12, 2))
    
    eaten_gram = fields.Float(string="Insect Gram", default=0.0000, digits=(12, 2), )
    eaten = fields.Float(compute='_percent_eaten',group_operator="avg", string="Insect_%", readonly=True, store=True, default=0.0000, digits=(12, 2))
    
    immature_gram = fields.Float(string="Immature Gram", default=0.0000, digits=(12, 2), )
    immature = fields.Float(compute='_percent_immature',group_operator="avg", string="Immature_%", readonly=True, store=True, default=0.0000, digits=(12, 2))
    
    sampler = fields.Char(string="Sampler", )
    maize_yn = fields.Char(string="Maize YN", )
    stone_count = fields.Float(string="Stone Count")
    stick_count = fields.Float(string="Stick Count")
    
    bb12_gram = fields.Float(string="BB12 Gram", default=0.0000, digits=(12, 2), )
    bb12 = fields.Float(compute='_percent_bb12', string="BB12_%", default=0.0000, digits=(12, 2), readonly=True, store=True)
    
    deduction = fields.Float(compute='_compute_deduction', string="Deduction %",  store=True,  digits=(12, 2),)
    deduction_manual = fields.Float(string="Deduction Manual %", digits=(12, 2), )
    remark = fields.Char(string="Remark")
    
    check_user = fields.Boolean('User Edit', compute='get_user')
    
    def get_user(self):
        if SUPERUSER_ID == self._uid:
            self.check_user = True
        else:
            self.check_user = False

    def update_sample_quality(self):
        for this in self:
            for grn in this.picking_ids:
                if grn.use_sample:
                    grn.kcs_sample_ids = [(4, this.id)]
                    if this.deduction_manual != 0:
                        grn.kcs_line.deduction_manual = this.deduction_manual
                        grn.kcs_line._compute_deduction()
                    else:
                        grn.kcs_line.deduction_manual = this.deduction
                        grn.kcs_line._compute_deduction()
        return True
    

        