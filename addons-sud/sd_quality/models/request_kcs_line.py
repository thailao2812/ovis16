# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

class RequestKCSLine(models.Model):
    _name = "request.kcs.line"
    _inherit = ['mail.thread'] #SON Add
    _order = 'id'
    
    @api.model
    def _default_uom_id(self):
        uom_id = self.env['uom.uom'].search([('id','=', 3)])
        return uom_id
    
    name = fields.Text("Name",readonly=True, states={'draft': [('readonly', False)]})
    product_id = fields.Many2one("product.product", string="Product", required=True)
    categ_id = fields.Many2one("product.category", string="Category",domain=[('parent_id','!=',False)])
    product_qty = fields.Float("Net Weight",digits=(12, 0))
    product_uom = fields.Many2one("uom.uom", string="UoM", required=True, default=_default_uom_id)
    #criterions_id = fields.Many2one("kcs.criterions", string="KCS Criterion",readonly=True, states={'draft': [('readonly', False)]})
    criterions_id = fields.Many2one(related='picking_id.kcs_criterions_id',  string="KCS Criterion",readonly=True, states={'draft': [('readonly', False)]})
    related='contract_line.price_unit', 
    indicator_kcs_ids = fields.One2many("indicator.kcs", "request_line_id", string="KCS Indicator" ,
                                        readonly=True, states={'draft': [('readonly', False)]})
    #request_id = fields.Many2one("request.kcs", string="Request KCS",   copy=False)
    picking_id = fields.Many2one("stock.picking", string="Request KCS", ondelete='cascade', index=True, copy=False)
    move_id = fields.Many2one('stock.move.line', string="Move Line", readonly=True, copy=False)
    cuptest = fields.Char(string="Cuptest")
    
    x_inspectator = fields.Many2one('x_inspectors.kcs', string='Inspected/Sampler')
    
    def _default_warehouse(self):
        warehouse_ids = self.env['stock.warehouse'].with_context(user_workers=True).search(
            [('company_id', '=', self.env.user.company_id.id)])
        # default with user only working 1 company account analytic
        if warehouse_ids:
            return warehouse_ids[0]
    
    @api.model
    def _domain_warehouse(self):
        return "[('id', 'in', %s)]" % self.env.user._warehouses_domain()
    
    x_warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', related='picking_id.warehouse_id', store=True)
    
    
    inspector = fields.Char(string="Inspector", required=False)
    x_certificate_id = fields.Many2one(related='picking_id.certificate_id', string='Certificate')
    p_contract_id = fields.Many2one('s.contract', 'P Contract')
    
    x_bulk_density = fields.Char(string='Density (grm/ml)', size=256)
    
    check_user = fields.Boolean('User Edit', compute='get_user')
    x_label = fields.Char(string="   ")
    
    state_kcs = fields.Selection(selection=[('draft', 'New'),('approved', 'Approved'),
        ('rejected', 'Rejected'),('cancel', 'Cancel')],string='KCS Status', readonly=True, copy=False, index=True, default='draft')
    
    reference = fields.Char(string="Warehouse Delivery")
    p_contract = fields.Many2one('s.contract', 'P Contract', related='picking_id.pcontract_id',
                                 store=True, readonly=True)
    
    packing_id = fields.Many2one('ned.packing', string='Packing')
    bag_no = fields.Float(string="Bag nos.",digits=(12, 0))
    remark = fields.Char(string="Remark")

    def get_user(self):
        for rc in self:
            rc.check_user = False  
            return
            if rc.user_has_groups('ned_kcs.group_manager_qc_button'):
                rc.check_user = True
            else:
                rc.check_user = False  
    
    def unlink(self):
        for request_line in self:
            if request_line.state not in ('draft', 'cancel'):
                raise UserError(_('You can only delete draft or cancel.'))
        return super(RequestKCSLine, self).unlink()
    
    def button_load(self):
        if self.criterions_id:
            self.env.cr.execute('''DELETE FROM indicator_kcs WHERE request_line_id = %s''' % (self.id))
            for criterions_line in self.criterions_id.ksc_line_ids:
                var = {'check_indicators': criterions_line.check_indicators or False, 'standard': criterions_line.value or 0.0,
                       'type': criterions_line.type or False, 'request_line_id': self.id, 'measured_value': 0.0}
                self.env['indicator.kcs'].create(var)
        return True
    
    @api.onchange("product_id")
    def onchange_product_id(self):
        tmpl = self.env['product.template']
        if not self.product_id:
            values =  {'categ_id': False}
            self.update(values)
        tmpl_obj = tmpl.browse(self.product_id.product_tmpl_id.id)
        categ_id = tmpl_obj.categ_id.id or False
        values =  {'categ_id': categ_id}
        self.update(values)
            
    def button_approved(self):
        if not self.move_id and not self.criterions_id:
            raise UserError(_('Unable to approved GRN Quality'))
        self.write({'state': 'approved', 'user_approve': self.env.uid,'date_approve': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
                
    def button_reject(self):
        if self.criterions_id.state == 'done' or self.move_id.state == 'done': 
            raise UserError(_('Unable to cancel GRN Quality'))
        self.write({'state': 'cancel'})
    
    
    def set_to_draft(self):
        self.state ='draft'
        
    def btt_qc_modification(self):
        if self.picking_id:
            self.picking_id.btt_qc_modification()
    
    
    
    state = fields.Selection(selection=[('draft', 'New'),('approved', 'Approved'),('reject', 'Reject')],string='Status', readonly=True, copy=False, 
                    index=True, default='draft', )
    
    sample_weight = fields.Float(string="Sample Weight", default=0.0000, digits=(12, 2), )
    bb_sample_weight = fields.Float(string="BB Sample Weight", default=0.0000, digits=(12, 2), )
    
    @api.constrains('sample_weight')
    def _constrains_sample_weight(self):
        for obj in self:
            if obj.sample_weight == 1000:
                raise ValidationError(_('sample_weight between 0 and  1000'))
    
    @api.constrains('bb_sample_weight')
    def _constrains_bb_sample_weight(self):
        for obj in self:
            if obj.bb_sample_weight == 1000:
                raise ValidationError(_('bb_sample_weight between 0 and 1000'))
            
    
    mc_degree = fields.Float(string="MCDegree", default=0.0000, digits=(12, 2), tracking= True )
    mc = fields.Float(compute='_percent_mc', string="MC_%", readonly=True, store=True, default=0.0000, digits=(12, 2), tracking= True)
    mc_deduct = fields.Float(compute='_mc_deduct', string="MC Deduct", readonly=True, store=True, default=0.0000, digits=(12, 2), tracking= True)
    
    fm_gram = fields.Float(string="FM Gram", default=0.0000, digits=(12, 2),tracking= True )
    fm = fields.Float(compute='_percent_fm',string="FM_%", readonly=True, store=True, default=0.0000, digits=(12, 2),group_operator="avg", tracking= True)
    fm_deduct = fields.Float(compute='_fm_deduct', string="FM Deduct", readonly=True, store=True, default=0.0000, digits=(12, 2), tracking= True)
    
    black_gram = fields.Float(string="Black Gram", default=0.0000, digits=(12, 2), tracking= True)
    black = fields.Float(compute='_percent_black',group_operator="avg",string="Black_%", readonly=True, store=True, default=0.0000, digits=(12, 2), tracking= True)
    
    broken_gram = fields.Float(string="Broken Gram", default=0.0000, digits=(12, 2), tracking= True)
    broken = fields.Float(compute='_percent_broken',group_operator="avg",string="Broken_%", readonly=True, store=True, default=0.0000, digits=(12, 2), tracking= True)
    broken_deduct = fields.Float(compute='_broken_deduct', string="BB Deduct", readonly=True, store=True, default=0.0000, digits=(12, 2), tracking= True)
    
    brown_gram = fields.Float(string="Brown Gram", default=0.0000, digits=(12, 2),tracking= True ) 
    brown = fields.Float(compute='_percent_brown',group_operator="avg",string="Brown_%", readonly=True, store=True, default=0.0000, digits=(12, 2), tracking= True)
    brown_deduct = fields.Float(compute='_brown_deduct',string="Brown Deduct", readonly=True, store=True, default=0.0000, digits=(12, 2), tracking= True)
    
    bbb = fields.Float(compute='_bbb_deduct',string="BBB", readonly=True, store=True, default=0.0000, digits=(12, 2), tracking= True)
    
    mold_gram = fields.Float(string="Mold Gram", default=0.0000, digits=(12, 2), tracking= True)
    mold = fields.Float(compute='_percent_mold',group_operator="avg",string="Mold_%", readonly=True, store=True, default=0.0000, digits=(12, 2), tracking= True)
    mold_deduct = fields.Float(compute='_mold_deduct',string="Mold Deduct", readonly=True, store=True, default=0.0000, digits=(12, 2), tracking= True)
        
    cherry_gram = fields.Float(string="Cherry Gram", default=0.0000, tracking= True)
    cherry = fields.Float(compute='_percent_cherry', group_operator="avg",string="Cherry_%", readonly=True, store=True, default=0.0000, digits=(12, 2), tracking= True)
    
    excelsa_gram = fields.Float(string="Excelsa Gram", default=0.0000, digits=(12, 2),tracking= True )
    excelsa = fields.Float(compute='_percent_excelsa', group_operator="avg", string="Excelsa_%", readonly=True, store=True, default=0.0000, digits=(12, 2), tracking= True)
    excelsa_deduct = fields.Float(compute='_excelsa_deduct' ,string="Excelsa Deduct", readonly=True, store=True, default=0.0000, digits=(12, 2), tracking= True)
    
    screen20_gram = fields.Float(string="Screen20 Gram", default=0.0000, digits=(12, 2), tracking= True)
    screen20 = fields.Float(compute='_percent_screen20',group_operator="avg", string="Screen20_%", readonly=True, store=True, default=0.0000, digits=(12, 2), tracking= True)
    
    screen19_gram = fields.Float(string="Screen19 Gram", default=0.0000, digits=(12, 2),tracking= True )
    screen19 = fields.Float(compute='_percent_screen19',group_operator="avg", string="Screen19_%", readonly=True, store=True, default=0.0000, digits=(12, 2), tracking= True)

    screen18_gram = fields.Float(string="Screen18 Gram", default=0.0000, digits=(12, 2), tracking= True)
    screen18 = fields.Float(compute='_percent_screen18',group_operator="avg", string="Screen18_%", readonly=True, store=True, default=0.0000, digits=(12, 2), tracking= True)
    oversc18 = fields.Float(compute='_screen18_deduct',string="OverSc18 Deduct", readonly=True, store=True, default=0.0000, digits=(12, 2), tracking= True)

    screen17_gram = fields.Float(string="Screen17 Gram", default=0.0000,
                                 digits=(12, 2), tracking= True)
    screen17 = fields.Float(compute='_percent_screen17', group_operator="avg",
                            string="Screen17 %", readonly=True, store=True,
                            default=0.0000, digits=(12, 2), tracking= True)

    screen16_gram = fields.Float(string="Screen16 Gram", default=0.0000, digits=(12, 2), tracking= True)
    screen16 = fields.Float(compute='_percent_screen16',group_operator="avg", string="Screen16 %", readonly=True, store=True, default=0.0000, 
                            tracking= True, digits=(12, 2))
    oversc16 = fields.Float(compute='_screen16_deduct',string="OverSc16 Deduct", readonly=True, store=True, tracking= True, default=0.0000, digits=(12, 2))
    screen15_gram = fields.Float(string="Screen15 Gram", default=0.0000,
                                 digits=(12, 2), )
    screen15 = fields.Float(compute='_percent_screen15', group_operator="avg",
                            string="Screen15 %", readonly=True, store=True, tracking= True,
                            default=0.0000, digits=(12, 2))
    screen14_gram = fields.Float(string="Screen14 Gram", default=0.0000,
                                 digits=(12, 2), tracking= True)
    screen14 = fields.Float(compute='_percent_screen14', group_operator="avg",
                            string="Screen14 %", readonly=True, store=True, tracking= True,
                            default=0.0000, digits=(12, 2))
    screen13_gram = fields.Float(string="Screen13 Gram", default=0.0000, digits=(12, 2), tracking= True)
    screen13 = fields.Float(compute='_percent_screen13',group_operator="avg", string="Screen13_%", readonly=True, store=True,tracking= True,
                             default=0.0000, digits=(12, 2))
    oversc13 = fields.Float(compute='_screen13_deduct',string="OverSc13 Deduct", readonly=True, store=True, default=0.0000, digits=(12, 2), tracking= True)
    
    # greatersc12_gram = fields.Float(string="Screen12 Gram", default=0.000, digits=(12, 2), )
    greatersc12_gram = fields.Float(compute='_greatersc12_gram',group_operator="avg", string="Screen12 Gram", readonly=True, store=True, default=0.000, 
                                    tracking= True, digits=(12, 2))
    greatersc12 = fields.Float(compute='_percent_greatersc12',group_operator="avg", string="Screen12_%", readonly=True, store=True,tracking= True, default=0.000)

    belowsc12_gram = fields.Float(string="Belowsc12 Gram", default=0.000, digits=(12, 2), )
    belowsc12 = fields.Float(compute='_percent_belowsc12',group_operator="avg", string="Belowsc12_%", readonly=True, store=True, default=0.000)
    oversc12 = fields.Float(compute='_screen12_deduct',string="OverSc12 Deduct", readonly=True, store=True, default=0.0000, digits=(12, 2))
    
    burned_gram = fields.Float(string="Burned Gram", default=0.0000, digits=(12, 2), tracking= True)
    burned = fields.Float(compute='_percent_burned',group_operator="avg", string="Burned_%", default=0.0000, digits=(12, 2),store=True, tracking= True)
    burned_deduct = fields.Float(compute='_burned_deduct',string="Burned Deduct",  store=True,  digits=(12, 2), tracking= True)
    
    #24/11 Kiệt Điều chỉnh thêm Rule QC 
    ligh_burnded_bean_gram = fields.Float(string="Ligh Burnded Bean Gram", default=0.0000, digits=(12, 2), tracking= True)
    ligh_burnded_bean = fields.Float(compute='_percent_ligh_burnded_bean',group_operator="avg", string="Ligh Burnded Bean_%", default=0.0000, digits=(12, 2),store=True, tracking= True)
    ligh_burnded_bean_result = fields.Selection([('pass','Pass'),('rejected','Rejected')], compute='_ligh_burnded_bean_result', string="Ligh Burnded Bean Result", tracking= True, store= True)
                                            
    
    eaten_gram = fields.Float(string="Insect Bean Gram", default=0.0000, digits=(12, 2),tracking= True )
    eaten = fields.Float(compute='_percent_eaten',group_operator="avg", string="Insect Bean_%", tracking= True, readonly=True, store=True, 
                         default=0.0000, digits=(12, 2))
    # insect_bean_gram = fields.Float(string="Insect bean Gram", default=0.0000, digits=(12, 2), )
    # insect_bean = fields.Float(compute='_insect_bean',group_operator="avg",string="Insect bean_%", readonly=True, store=True, default=0.0000, digits=(12, 2))
    insect_bean_deduct = fields.Float(compute='_eaten_deduct',string="Insect Bean Deduct", readonly=True,tracking= True, store=True, 
                                      default=0.0000, digits=(12, 2))
    
    immature_gram = fields.Float(string="Immature Gram", default=0.0000, digits=(12, 2),tracking= True )
    immature = fields.Float(compute='_percent_immature',group_operator="avg", string="Immature_%", tracking= True,readonly=True, store=True, 
                            default=0.0000, digits=(12, 2))
    
    sampler = fields.Char(string="Analysis By", tracking= True )
    maize_yn = fields.Char(string="Maize YN", tracking= True )
    stone_count = fields.Float(string="Stone Count", tracking= True)
    stick_count = fields.Float(string="Stick Count", tracking= True)
    
    bb12_gram = fields.Float(string="BB12 Gram", default=0.0000, digits=(12, 2),tracking= True )
    bb12 = fields.Float(compute='_percent_bb12', string="BB12_%", default=0.0000, digits=(12, 2), readonly=True, store=True, tracking= True)
    
    deduction = fields.Float(compute='_compute_deduction', string="Deduction %",  store=True, digits=(12, 2), tracking= True)
    qty_reached = fields.Float(compute='_compute_deduction', string="Deduction Weight", store=True, digits=(12, 0), tracking= True)
    basis_weight = fields.Float(compute='_compute_deduction', string="Basis Weight", store=True, digits=(12, 0), tracking= True)
    deduction_manual = fields.Float(string="Deduction Manual %", digits=(12, 2), tracking= True)
    check_deduction = fields.Boolean(string="No Deduction %", tracking= True)
    
    stack_id = fields.Many2one('stock.lot',related='move_id.lot_id', string="Stack", readonly=True,store=True, tracking= True)
    zone_id = fields.Many2one('stock.zone',related='move_id.zone_id', string="Zone", readonly=True,store=True, tracking= True)
    partner_id = fields.Many2one('res.partner',related='picking_id.partner_id', string="Partner", readonly=True,store=True, tracking= True)
    date = fields.Datetime(related='picking_id.date_kcs', string="KCs Date", readonly=True,store=False, tracking= True)
    # Erro
    production_id = fields.Many2one('mrp.production',related='picking_id.production_id', string="Production", readonly=True,store=True)
    picking_type_id = fields.Many2one('stock.picking.type',related='picking_id.picking_type_id', string="Picking Type", readonly=True,store=True)
    picking_type_code = fields.Selection(related='picking_id.picking_type_id.code', 
                    selection=[('incoming', 'Suppliers'), ('outgoing', 'Customers'), ('internal', 'Internal')],string="Picking Type Code", readonly=True,store=True)
    cuptest = fields.Char(string="Cuptest", tracking= True)
    districts_id = fields.Many2one(related='picking_id.districts_id', string="districts", readonly=True,store=False)
    
    # err
    contract_no = fields.Char(related='picking_id.contract_no', string="Contract no", readonly=True)
    
    reference = fields.Char(string="Reference", tracking= True)
    
    origin_deduction = fields.Float(compute='_compute_deduction_origin',string='Origin Deduction',store=True)
    
    ###################################################################
    reject_mc = fields.Boolean(string="Reject mc", tracking= True)
    reject_foreign = fields.Boolean(string="Reject Foreign", tracking= True)
    reject_bb = fields.Boolean(string="Reject BB", tracking= True)
    reject_brown = fields.Boolean(string="Reject Brown", tracking= True)
    reject_mold = fields.Boolean(string="Reject Mold", tracking= True)
    reject_excelsa = fields.Boolean(string="Reject Excelsa", tracking= True)
    reject_burned = fields.Boolean(string="Reject Burned", tracking= True)
    reject_insect_bean = fields.Boolean(string="Reject Insect Bean", tracking= True)
    
    
    @api.depends('sample_weight','screen20_gram','screen19_gram','screen18_gram')
    def _total_s18(self):
        for this in self:
            screen20 = this._percent_screen20()
            screen19 = this._percent_screen19()
            screen18 = this._percent_screen18()
            this.total_S18 = screen20 + screen19 + screen18
            return screen20 + screen19 + screen18
        
    total_S18 = fields.Float(compute='_total_s18',group_operator="avg", string="Total S18%", 
                        readonly=True, store=True, default=0.0000, digits=(12, 2))
    
    
    @api.depends('sample_weight','screen20_gram','screen19_gram','screen18_gram', 'screen17_gram','screen16_gram')
    def _total_s16(self):
        for this in self:
            total_17 = this._percent_screen17() or 0.0
            total_16 = this._percent_screen16() or 0.0
            total_20_19_18 = this._total_s18()
            this.total_S16 = total_20_19_18 + total_17 + total_16
            return total_20_19_18 + total_17 + total_16
        
    total_S16 = fields.Float(compute='_total_s16',group_operator="avg", string="Total S16%", 
                        readonly=True, store=True, default=0.0000, digits=(12, 2))
    
    @api.depends('sample_weight','screen20_gram','screen19_gram','screen18_gram', 'screen17_gram','screen16_gram','screen15_gram','screen13_gram' )
    def _total_s13(self):
        for this in self:
            total_15 = this._percent_screen15() or 0.0
            total_13 = this._percent_screen13() or 0.0
            total_20_19_18_17_16 = this._total_s16()
            this.total_S13 = total_20_19_18_17_16 + total_15 + total_13
            return total_20_19_18_17_16 + total_15 + total_13
        
    total_S13 = fields.Float(compute='_total_s13',group_operator="avg", string="Total S13%", 
                        readonly=True, store=True, default=0.0000, digits=(12, 2))
    
    
    
    
    @api.depends('mc_degree')
    def _percent_mc(self):
        for this in self:
            if this.mc_degree > 0:
                this.mc = (this.mc_degree / (1 + this.mc_degree / 100)) 
            else:
                this.mc = 0.0
            this._mc_deduct()
            return this.mc
    
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
    
    
    @api.depends('sample_weight','fm_gram')
    def _percent_fm(self):
        for this in self:
            if this.sample_weight != 0:
                this.fm = (this.fm_gram / this.sample_weight or 0.0000)*100
            else:
                this.fm = 0.0
            return this.fm
    
    
    # @api.depends('fm','criterions_id')
    # def _fm_deduct(self):
    #     for this in self:
    #         if this.fm > 0 and this.criterions_id:
    #             fm_deduct = deduct = percent_fm = 0.0000
    #             percent_fm = round(this.fm,2)
    #
    #             if this.criterions_id.foreign_matter_ids and this.criterions_id.reject_rule:
    #                 max_degree = max(this.criterions_id.foreign_matter_ids.mapped('range_end')) 
    #                 if percent_fm > max_degree:
    #                     this.reject_foreign = True
    #                 else: 
    #                     this.reject_foreign = False
    #             else: 
    #                 this.reject_foreign = False
    #
    #             if this.criterions_id.finished_products:
    #                 #Kiệt range +
    #                 self.env.cr.execute('''SELECT id FROM foreign_matter 
    #                     WHERE criterion_id = %s 
    #                     AND rule = 'addition'
    #                     ORDER BY range_end desc'''%(this.criterions_id.id))
    #                 for fm_standard in self.env.cr.dictfetchall(): 
    #                     deduct =0.0
    #                     fm_obj = self.env['foreign.matter'].browse(fm_standard['id'])
    #                     percent = fm_obj.percent or 0.0
    #                     if fm_obj.range_start <= percent_fm and  percent_fm <= fm_obj.range_end:
    #                         addition = (fm_obj.range_end - fm_obj.percent) 
    #                         fm_deduct = addition
    #                         this.fm_deduct = fm_deduct 
    #
    #                     if fm_deduct !=0:
    #                         continue
    #
    #                 #Kiệt range trư
    #                 self.env.cr.execute('''SELECT id FROM foreign_matter WHERE criterion_id = %s AND rule = 'subtraction' ORDER BY range_end desc'''%(this.criterions_id.id))
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
    #                 #Kiệt range trư
    #                 addition = 0
    #                 if percent_fm >=1:
    #                     self.env.cr.execute('''SELECT id FROM foreign_matter WHERE criterion_id = %s AND rule = 'subtraction'  AND range_start >= 1 ORDER BY range_end desc'''%(this.criterions_id.id))
    #                     for fm_standard in self.env.cr.dictfetchall(): 
    #                         deduct =0.0
    #                         fm_obj = self.env['foreign.matter'].browse(fm_standard['id'])
    #                         percent = fm_obj.percent or 0.0
    #                         if fm_obj.range_start <= percent_fm and  percent_fm <= fm_obj.range_end:
    #                             deduct = (percent_fm - fm_obj.range_start) * (percent/100)
    #                             percent_fm = fm_obj.range_start
    #                         fm_deduct += deduct
    #                     this.fm_deduct = fm_deduct *(-1)
    #                 #Kiệt range +
    #                 else:
    #                     # sql ='''
    #                     #     SELECT id FROM foreign_matter WHERE criterion_id = %s AND rule = 'addition' ORDER BY range_end desc limit 1
    #                     # '''%(this.criterions_id.id)
    #                     fm_obj = self.env['foreign.matter'].search([('criterion_id','=',this.criterions_id.id),('rule','=','addition')], limit = 1)
    #                     if fm_obj:
    #                         deduct =0.0
    #                         percent = fm_obj.percent or 0.0
    #                         if fm_obj.range_start <= percent_fm and  percent_fm < fm_obj.range_end:
    #                             addition = (fm_obj.range_end - percent_fm) * fm_obj.percent /100
    #                         this.fm_deduct = addition 
    #         else:
    #             this.fm_deduct = 0.0
    #
    #         return this.fm_deduct
            
    @api.depends('fm','criterions_id')
    def _fm_deduct(self):
        for this in self:
            if this.fm > 0 and this.criterions_id:
                fm_deduct = deduct = percent_fm = 0.0000
                percent_fm = round(this.fm,2)
                
                if this.criterions_id.foreign_matter_ids and this.criterions_id.reject_rule:
                    max_degree = max(this.criterions_id.foreign_matter_ids.mapped('range_end')) 
                    if percent_fm > max_degree:
                        this.reject_foreign = True
                    else: 
                        this.reject_foreign = False
                else: 
                    this.reject_foreign = False
                        
                if this.criterions_id.finished_products:
                    #Kiệt range +
                    self.env.cr.execute('''SELECT id FROM foreign_matter 
                        WHERE criterion_id = %s 
                        AND rule = 'addition'
                        ORDER BY range_end desc'''%(this.criterions_id.id))
                    for fm_standard in self.env.cr.dictfetchall(): 
                        deduct =0.0
                        fm_obj = self.env['foreign.matter'].browse(fm_standard['id'])
                        percent = fm_obj.percent or 0.0
                        if fm_obj.range_start <= percent_fm and  percent_fm <= fm_obj.range_end:
                            addition = (fm_obj.range_end - fm_obj.percent) 
                            fm_deduct = addition
                            this.fm_deduct = fm_deduct 
                        
                        if fm_deduct !=0:
                            continue
                    
                    #Kiệt range trư
                    self.env.cr.execute('''SELECT id FROM foreign_matter WHERE criterion_id = %s AND rule = 'subtraction' ORDER BY range_end desc'''%(this.criterions_id.id))
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
                    #Kiệt range trư
                    addition = 0
                    if percent_fm >=1:
                        self.env.cr.execute('''SELECT id FROM foreign_matter WHERE criterion_id = %s AND rule = 'subtraction'  AND range_start >= 1 ORDER BY range_end desc'''%(this.criterions_id.id))
                        for fm_standard in self.env.cr.dictfetchall(): 
                            deduct =0.0
                            fm_obj = self.env['foreign.matter'].browse(fm_standard['id'])
                            percent = fm_obj.percent or 0.0
                            if fm_obj.range_start <= percent_fm and  percent_fm <= fm_obj.range_end:
                                deduct = (percent_fm - fm_obj.range_start) * (percent/100)
                                percent_fm = fm_obj.range_start
                            fm_deduct += deduct
                        this.fm_deduct = fm_deduct *(-1)
                    #Kiệt range +
                    else:
                        # sql ='''
                        #     SELECT id FROM foreign_matter WHERE criterion_id = %s AND rule = 'addition' ORDER BY range_end desc limit 1
                        # '''%(this.criterions_id.id)
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

    @api.depends('black','broken','brown','criterions_id')
    def _broken_deduct(self):
        for this in self:
            if this.black > 0 and this.broken > 0 and this.criterions_id:
                broken_deduct = deduct = percent_bb = 0.0000
                percent_bb = this.black + this.broken 
                
                if this.criterions_id.broken_standard_ids and this.criterions_id.reject_rule:
                    max_degree = max(this.criterions_id.broken_standard_ids.mapped('range_end')) 
                    if percent_bb > max_degree:
                        this.reject_bb = True
                    else:
                        this.reject_bb = False
                
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
            
            if this.criterions_id.brown_standard_ids and this.criterions_id.reject_rule:
                max_degree = max(this.criterions_id.brown_standard_ids.mapped('range_end')) 
                if this.brown > max_degree:
                    this.reject_brown = True
                else:
                    this.reject_brown = False
            else: 
                this.reject_brown = False
                    
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
                
                if this.criterions_id.mold_standard_ids and this.criterions_id.reject_rule:
                    max_degree = max(this.criterions_id.mold_standard_ids.mapped('range_end')) 
                    if percent_brown > max_degree:
                        this.reject_mold = True
                    else:
                        this.reject_mold = False
                else: 
                    this.reject_foreign = False
                
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
                percent_excelsa = this.excelsa
                
                if this.criterions_id.excelsa_standard_ids and this.criterions_id.reject_rule:
                    max_degree = max(this.criterions_id.excelsa_standard_ids.mapped('range_end')) 
                    if percent_excelsa > max_degree:
                        this.reject_excelsa = True
                    else:
                        this.reject_excelsa = False
                else: 
                    this.reject_excelsa = False
                
                self.env.cr.execute('''SELECT id FROM excelsa_standard WHERE criterion_id = %s ORDER BY range_end DESC'''%(this.criterions_id.id))
                for excelsa_standard in self.env.cr.dictfetchall():
                    excelsa_obj = self.env['excelsa.standard'].browse(excelsa_standard['id'])
                    deduct =0.0
                        
                    if excelsa_obj.range_start <= percent_excelsa and percent_excelsa <= excelsa_obj.range_end:
                        deduct = (percent_excelsa - excelsa_obj.range_start) * (excelsa_obj.percent/100 or 0.0)
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

    @api.depends('screen20','screen19','screen18','criterions_id')
    def _screen18_deduct(self):
        for this in self:
            if this.criterions_id.finished_products:
                if this.screen18 > 0 and this.criterions_id:
                    oversc18 = percent_oversc = standard = percent = 0.0000
        
                    percent_oversc = this.screen18 + this.screen19 + this.screen20
                    standard = this.criterions_id.standard_screen18
                    percent = this.criterions_id.percent_screen18

                    if percent_oversc < standard:
                        oversc18 = (standard - percent_oversc) * percent /100
                        this.oversc18 = oversc18 * (-1) 
                else:
                    this.oversc18 = 0
            else:
                if this.screen18 > 0 and this.criterions_id:
                    oversc18 = percent_oversc = standard = percent = 0.0000
        
                    # percent_oversc = this.screen18
                    percent_oversc = this.screen18 + this.screen19 + this.screen20
                    standard = this.criterions_id.standard_screen18
                    percent = this.criterions_id.percent_screen18

                    if percent_oversc < standard:
                        this.oversc18 = (standard - percent_oversc) * percent /100 * (-1)

                    # if this.screen16 + this.screen18 + this.screen19 + this.screen20 >= 45:
                    #     this.oversc18 = 0
                    # else:
                    #     this.oversc18  = float_round(oversc18 * (-1), precision_rounding=0.01, rounding_method='UP')
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
            
    @api.depends('screen16','screen17','screen18','screen19','screen20','criterions_id')
    def _screen16_deduct(self):
        for this in self:
            if this.screen16 > 0 and this.criterions_id:
                oversc16 = percent_oversc = standard = standard18 = percent = scr181920 = 0.0000
    
                percent_oversc = this.screen16
                standard = this.criterions_id.standard_screen18_16
                standard18 = this.criterions_id.standard_screen18
                percent = this.criterions_id.percent_screen18_16
                if 0 < percent_oversc and  percent_oversc < standard - standard18:
                    oversc16 = (standard - standard18 - percent_oversc) * (percent/100 or 0.0)
                
                if this.screen16 + this.screen17 + this.screen18 + this.screen19 + this.screen20 < standard:
                    scr181920 = this.screen17 + this.screen18 + this.screen19 + this.screen20
                    oversc16 = (standard - scr181920 - percent_oversc) * (percent/100 or 0.0)
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
            
    @api.depends('screen13', 'screen14', 'screen15','screen16', 'screen17','screen18','screen19','screen20','criterions_id')
    def _screen13_deduct(self):
        for this in self:
            if this.criterions_id.finished_products:
                if this.screen13 > 0 and this.criterions_id:
                    oversc13 = percent_oversc = standard = percent = 0.0000
                    
                    percent_oversc = this.screen16 + this.screen17 + this.screen18 + this.screen13 + this.screen14 + this.screen15 + this.screen19 + this.screen20
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
                    if this.screen16 + this.screen17 + this.screen18 + this.screen13 + this.screen14 + this.screen15 + this.screen19 + this.screen20 < 90:
                        oversc13 = (standard - (this.screen16 + this.screen17 +  this.screen18 + this.screen19 + this.screen20 + this.screen13 + this.screen14 + this.screen15)) * (percent/100 or 0.0)
                        this.oversc13 = oversc13 * (-1) 
                    else:
                        this.oversc13 = 0
            return this.oversc13

    @api.depends('sample_weight','screen19_gram','screen20_gram','screen18_gram','screen16_gram','screen13_gram','belowsc12_gram', 'screen14_gram', 'screen15_gram', 'screen17_gram')
    def _greatersc12_gram(self):
        for this in self:
            if this.sample_weight > 0 and (this.screen20_gram + this.screen19_gram + this.screen18_gram + this.screen16_gram + this.screen13_gram + this.belowsc12_gram + this.screen14_gram + this.screen15_gram + this.screen17_gram) < this.sample_weight:
                this.greatersc12_gram = this.sample_weight - (this.screen20_gram + this.screen19_gram + this.screen18_gram + this.screen16_gram + this.screen13_gram + this.belowsc12_gram + this.screen14_gram + this.screen15_gram + this.screen17_gram)
            else:
                this.greatersc12_gram = 0.0
                
            if this.sample_weight > 0 and (this.screen20_gram + this.screen19_gram + this.screen18_gram + this.screen16_gram + this.screen13_gram + this.belowsc12_gram + this.screen14_gram + this.screen15_gram + this.screen17_gram) == 0:
                this.greatersc12_gram = 0.0
            self._percent_greatersc12()

    @api.depends('sample_weight','greatersc12_gram')
    def _percent_greatersc12(self):
        for this in self:
            if this.sample_weight > 0 and this.greatersc12_gram > 0:
                greatersc12 = this.greatersc12_gram / this.sample_weight or 0.0000
                this.greatersc12 = greatersc12 * 100
            else:
                this.greatersc12 = 0.0

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
    
    @api.depends('sample_weight','ligh_burnded_bean_gram')
    def _percent_ligh_burnded_bean(self):
        for this in self:
            if this.sample_weight > 0 and this.ligh_burnded_bean_gram > 0:
                this.ligh_burnded_bean = (this.ligh_burnded_bean_gram / this.sample_weight or 0.0000) * 100
            else:
                this.ligh_burnded_bean = 0.0
            
            this._ligh_burnded_bean_result()
            return this.ligh_burnded_bean
    
    @api.depends('ligh_burnded_bean','criterions_id')
    def _ligh_burnded_bean_result(self):
        for this in self:
            if this.ligh_burnded_bean and this.criterions_id:
                self.env.cr.execute('''SELECT id FROM ligh_burnded_bean WHERE criterion_id = %s ORDER BY range_end DESC'''%(this.criterions_id.id))
                for ligh_burnded_bean in self.env.cr.dictfetchall():
                    ligh_burnded_bean_obj = self.env['ligh.burnded.bean'].browse(ligh_burnded_bean['id'])
                    if ligh_burnded_bean_obj.range_start <= this.ligh_burnded_bean and this.ligh_burnded_bean <= ligh_burnded_bean_obj.range_end:
                        this.ligh_burnded_bean_result = 'pass'
                    else:
                        this.ligh_burnded_bean_result = 'rejected'
            
    @api.depends('burned','burned_gram','sample_weight')
    def _burned_deduct_old(self):
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
    
    
    @api.depends('burned','burned_gram','sample_weight')
    def _burned_deduct(self):
        for this in self:
            if this.burned and this.criterions_id:
                burned_deduct = percent_burned = standard = percent = 0.0000
                percent_burned = this.burned 
                
                if this.criterions_id.burned_deduct_ids and this.criterions_id.reject_rule:
                    max_degree = max(this.criterions_id.burned_deduct_ids.mapped('range_end')) 
                    if percent_burned > max_degree:
                        this.reject_burned = True
                    else:
                        this.reject_burned = False
                else: 
                    this.reject_burned = False
                
                self.env.cr.execute('''SELECT id FROM burned_deduct WHERE criterion_id = %s ORDER BY range_end DESC'''%(this.criterions_id.id))
                for burned_deduct_line in self.env.cr.dictfetchall():
                    burned_obj = self.env['burned.deduct'].browse(burned_deduct_line['id'])
                    deduct =0.0
                        
                    if burned_obj.range_start <= percent_burned and percent_burned <= burned_obj.range_end:
                        deduct = (percent_burned - burned_obj.range_start) * (burned_obj.percent/100 or 0.0)
                        percent_burned = burned_obj.range_start
                    burned_deduct += deduct
                this.burned_deduct = burned_deduct *(-1)
            else:
                this.burned_deduct = 0.0
            return this.burned_deduct
    
    @api.depends('bb_sample_weight','eaten_gram')
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
    def _eaten_deduct(self):
        for this in self:
            if this.eaten > 0 and this.criterions_id:
                insect_bean_deduct = insect_obj = percent_insect_bean = 0.0000
                percent_insect_bean = round(this.eaten, 2)
                
                if this.criterions_id.insect_bean_ids and this.criterions_id.reject_rule:
                    max_degree = max(this.criterions_id.insect_bean_ids.mapped('range_end')) 
                    if percent_insect_bean > max_degree:
                        this.reject_insect_bean = True
                    else:
                        this.reject_insect_bean = False
                
                else: 
                    this.reject_insect_bean = False
                
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
            
    # @api.depends('sample_weight','insect_bean_gram')
    # def _insect_bean(self):
    #     for this in self:
    #         if this.sample_weight != 0:
    #             insect_bean_gram = this.insect_bean_gram / this.sample_weight  or 0.0000
    #             this.insect_bean = insect_bean_gram * 100
    #         else:
    #             this.insect_bean = 0.0
    #         return this.insect_bean
            
    # @api.depends('insect_bean','criterions_id')
    # def _insect_bean_deduct(self):
    #     for this in self:
    #         if this.insect_bean > 0 and this.criterions_id:
    #             insect_bean_deduct = insect_obj = percent_insect_bean = 0.0000
    #             percent_insect_bean = this.insect_bean
                
    #             if percent_insect_bean >=1:
    #                 self.env.cr.execute('''SELECT id FROM insect_bean WHERE criterion_id = %s AND range_start >= 1 ORDER BY range_end desc'''%(this.criterions_id.id))
    #                 for fm_standard in self.env.cr.dictfetchall(): 
    #                     deduct =0.0
    #                     insect_obj = self.env['insect.bean'].browse(fm_standard['id'])
    #                     percent = insect_obj.percent or 0.0
    #                     if insect_obj.range_start <= percent_insect_bean and  percent_insect_bean <= insect_obj.range_end:
    #                         deduct = (percent_insect_bean - insect_obj.range_start) * (percent/100)
    #                         percent_insect_bean = insect_obj.range_start
    #                     insect_bean_deduct += deduct
    #                 this.insect_bean_deduct = insect_bean_deduct *(-1)
                    
    #             else:
    #                 self.env.cr.execute('''SELECT id FROM insect_bean WHERE criterion_id = %s AND range_start <= 0.9 ORDER BY range_end desc'''%(this.criterions_id.id))
    #                 for fm_standard in self.env.cr.dictfetchall(): 
    #                     deduct =0.0
    #                     insect_obj = self.env['insect.bean'].browse(fm_standard['id'])
    #                     percent = insect_obj.percent or 0.0
    #                     if insect_obj.range_start <= percent_insect_bean and  percent_insect_bean < insect_obj.range_end:
    #                         deduct = (1 - percent_insect_bean) * (percent/100)
    #                         percent_insect_bean = insect_obj.range_start
    #                     insect_bean_deduct += deduct
    #                 this.insect_bean_deduct = insect_bean_deduct
    #         else:
    #             this.insect_bean_deduct = 0.0
    #         return this.insect_bean_deduct

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
                
    @api.onchange('check_deduction')
    def _onchange_check_deducttion(self):
        for this in self:
            if this.check_deduction == True:
                this.deduction_manual = 0
                this.deduction = 0
            # return [this.deduction_manual, this.deduction]
                
    @api.onchange('deduction_manual')
    def _onchange_deducttion_manual(self):
        for this in self:
            if this.deduction_manual != 0:
                this.check_deduction = False
            return this.check_deduction
    
    @api.depends('sample_weight','bb_sample_weight','mc_deduct','fm_deduct','broken_deduct','brown_deduct','check_deduction','picking_id.use_sample'
                 ,'mold_deduct','excelsa_deduct','oversc16','oversc13','burned_deduct','deduction_manual','oversc12','oversc18','insect_bean_deduct')
    def _compute_deduction(self):   
        for line in self:
            product_qty = line.product_qty or 0.0
            if line.picking_id.picking_type_id.deduct:
                if line.check_deduction == True:
#                     line.deduction_manual = 0
#                     line.deduction = 0
                    line.qty_reached = product_qty * line.deduction_manual/100 or 0.0
                    line.basis_weight = product_qty + product_qty * line.deduction_manual/100 or 0.0
                if line.deduction_manual != 0:
#                     line.check_deduction = False
                    line.deduction = line.deduction_manual
                    
                    line.qty_reached = product_qty * line.deduction_manual/100 or 0.0
                    line.basis_weight = product_qty + product_qty * line.deduction_manual/100 or 0.0
                if line.check_deduction == False and line.deduction_manual == 0:
                    deduction = 0.0
                    if line.picking_id.use_sample == False:
                        deduction = (line.mc_deduct + line.fm_deduct + line.broken_deduct +
                                    line.brown_deduct + line.mold_deduct + line.excelsa_deduct + line.insect_bean_deduct +
                                    line.oversc13 + line.oversc16 + line.burned_deduct  + line.oversc18 + line.oversc12) or 0.0
                        line.deduction = deduction
                    else:
                        deduction = line.deduction_manual
                    line.qty_reached = product_qty * deduction/100 or 0.0
                    line.basis_weight = product_qty + product_qty * deduction/100 or 0.0
            else:
                line.qty_reached = product_qty
                line.basis_weight = product_qty
            return [line.qty_reached, line.basis_weight]
    
    @api.depends('sample_weight','bb_sample_weight','mc_deduct','fm_deduct','broken_deduct','brown_deduct'
                 ,'mold_deduct','excelsa_deduct','oversc16','oversc13','burned_deduct','oversc12','oversc18','insect_bean_deduct','state','state_kcs')
    def _compute_deduction_origin(self):   
        for line in self:
            if line.picking_id.picking_type_id.deduct:
                deduction = (line.mc_deduct + line.fm_deduct + line.broken_deduct +
                      line.brown_deduct + line.mold_deduct + line.excelsa_deduct + line.insect_bean_deduct +
                       line.oversc13 + line.oversc16 + line.burned_deduct  + line.oversc18 + line.oversc12) or 0.0
                line.origin_deduction = deduction
            return line.origin_deduction
    
    @api.depends('broken','black','brown','criterions_id')
    def _bbb_deduct(self):
        for this in self:
            if not this.criterions_id.finished_products:
                if (this.broken + this.black) < 5 and (this.broken + this.black + this.brown)  <= 11 and this.criterions_id:
                    this.bbb =0
                else:
                    this.bbb = this.broken_deduct + this.brown_deduct
                return this.bbb
            
        