# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from datetime import datetime
from pytz import timezone
from dateutil.relativedelta import relativedelta
from datetime import timedelta
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT




DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
from lxml import etree
import base64
import qrcode
from io import BytesIO
import xlrd
import math
utr = [' ',',','.','/','<','>','?',':',';','"',"'",'[','{','}',']','=','+','-','_',')','(','*','&','^','%','$','#','@','!','`','~','|']
"""
Used for queue incoming trucks and collect truck data. 
Requiring approval from procurement staff for converting to GRN form.
"""
class NedSecurityGateQueue(models.Model):
    _name = "ned.security.gate.queue"
    _description = "Security Gate Queue"
    _order = "create_date desc"
    _inherit = ['mail.thread']
    
    def _get_printed_report_name(self):
        report_name = (_('%s')%(self.name))
        return report_name
    
    def picking_type_id_get_default(self):
        if self.warehouse_id:
            warehouse_id =self.warehouse_id.id
        else:
            warehouse_ids = self.env['stock.warehouse'].with_context(user_workers=True).search(
                [('company_id', '=', self.env.user.company_id.id)])
            # default with user only working 1 company account analytic
            if warehouse_ids:
                warehouse_id = warehouse_ids[0].id
            else:
                raise
        res = self.env['stock.picking.type'].search([('code','=','incoming'),('operation','=','factory'),('warehouse_id','=',warehouse_id)])
        return res.id or False
    
    @api.onchange('warehouse_id')
    def onchange_warehouse(self):
        if self.warehouse_id:
            # print(self.env.context.get('default_type_transfer')=='queue-exstore')
            code_type=''
            if self.env.context.get('default_type_transfer')=='queue':
                code_type = 'incoming'
            elif self.env.context.get('default_type_transfer')=='queue-exstore':
                code_type = 'outgoing'

            res = self.env['stock.picking.type'].search([('code','=',code_type),('operation','=','factory'),('warehouse_id','=',self.warehouse_id.id)])
            self.picking_type_id =res.id
    
    def _default_warehouse(self):
        warehouse_ids = self.env['stock.warehouse'].with_context(user_workers=True).search(
            [('company_id', '=', self.env.user.company_id.id)])
        # default with user only working 1 company account analytic
        if warehouse_ids:
            return warehouse_ids[0]
    
    @api.model
    def _domain_warehouse(self):
        return "[('id', 'in', %s)]" % self.env.user._warehouses_domain()
        
    warehouse_id = fields.Many2one('stock.warehouse',string="Warehouse",  readonly = True,required=True,
                                    states={'draft': [('readonly', False)], 'wh_approved': [('readonly', False)]} ,
                                    default=_default_warehouse, domain=lambda self: self._domain_warehouse())
    
    #24/11 Kiệt Điều chỉnh thêm Rule QC 
    ligh_burnded_bean_gram = fields.Float(string="Ligh Burnded Bean Gram", default=0.0000, digits=(12, 2), tracking= True)
    ligh_burnded_bean = fields.Float(compute='_percent_ligh_burnded_bean',group_operator="avg", string="Ligh Burnded Bean_%", default=0.0000, digits=(12, 2),store=True, tracking= True)
    ligh_burnded_bean_result = fields.Selection([('pass','Pass'),('rejected','Rejected')], compute='_ligh_burnded_bean_result', string="Ligh Burnded Bean Result", tracking= True, store= True)
    
    
    
    # Fields
    name = fields.Char(string="Name", readonly=True, required=True, copy=False, default='New')
    supplier_id = fields.Many2one('res.partner', string='Supplier', states={'approved': [('readonly', True)]},
                                      domain=[('is_supplier_coffee','=',True)], tracking=True)
    picking_type_id = fields.Many2one('stock.picking.type', string='Picking Type',readonly = True,
                                      states={'draft': [('readonly', False)]}, 
                                      required=True, default=picking_type_id_get_default)
    license_plate = fields.Char(string='Vehicle No.', required=True, states={'approved': [('readonly', True)]}) 
    certificate_id = fields.Many2one('ned.certificate', string='Certificate', required=False,readonly = True,
                                      states={'draft': [('readonly', False)]})
    estimated_bags = fields.Integer(string='Estimated Bags', required=False,readonly = True,
                                      states={'draft': [('readonly', False)]})
    coffee_origins = fields.Char(string='Coffee Origins', required=False,readonly = True,
                                      states={'draft': [('readonly', False)]})
    driver_name = fields.Char(string='Driver Name', required=False, readonly = True,
                                      states={'draft': [('readonly', False)], 'logistics_confirm': [('readonly', False)]})
    additional_reference = fields.Char(string='Additional Reference', required=False,readonly = True,
                                      states={'draft': [('readonly', False)]})
    state = fields.Selection([("draft", "Draft"),("pur_approved", "Purchase"),("qc_approved", "QC"),("wh_approved", "WH"),("logistics_confirm", "Logistics Confirm"),
                            ("sec_confirm", "Sec Confirm"),("approved", "Approved"),("cancel", "Cancelled"),("closed", "Closed"),("reject", "Reject")], string="Status", 
                             readonly=True, copy=False, index=True, default='draft',)
    date_approve = fields.Date(string='Approval Date', readonly=True, copy=False)
    user_approve = fields.Many2one('res.users', string='User Approve', readonly=True, copy=False)
    parking_order = fields.Integer('Parking Order',readonly = True)
    arrivial_time = fields.Datetime('Arrival Time',readonly = True)
    approx_quantity = fields.Float('Estimated Quantity',readonly= True,states={'draft': [('readonly', False)]},required = False, digits=(12, 0))
    time_in = fields.Datetime('Time In',readonly = True)
    time_out = fields.Datetime('Time Out',readonly = True)
    security_id = fields.Many2one('res.users', string='Security', readonly=True, default=lambda self: self.env.user)
    remarks = fields.Text('Remarks')

    qc_approve_date = fields.Datetime(string='QC Approve Date')
    
    @api.depends('sample_weight','ligh_burnded_bean_gram')
    def _percent_ligh_burnded_bean(self):
        for this in self:
            if this.sample_weight > 0 and this.ligh_burnded_bean_gram > 0:
                this.ligh_burnded_bean = (this.ligh_burnded_bean_gram / this.sample_weight or 0.0000) * 100
            else:
                this.ligh_burnded_bean = 0.0
            
            this._ligh_burnded_bean_result()
            return this.ligh_burnded_bean
    
    @api.depends('ligh_burnded_bean')
    def _ligh_burnded_bean_result(self):
        for this in self:
            if this.ligh_burnded_bean:
                if this.ligh_burnded_bean <=6:
                    this.ligh_burnded_bean_result = 'pass'
                else:
                    this.ligh_burnded_bean_result = 'rejected'

    @api.depends('mc_degree')
    def _percent_mc(self):
        for this in self:
            if this.mc_degree > 0:
                this.mc = (this.mc_degree / (1 + this.mc_degree / 100)) 
            else:
                this.mc = 0.0
            return this.mc

    @api.depends('sample_weight','fm_gram')
    def _percent_fm(self):
        for this in self:
            if this.sample_weight != 0:
                this.fm = (this.fm_gram / this.sample_weight or 0.0000)*100
            else:
                this.fm = 0.0
            return this.fm

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

    @api.depends('bb_sample_weight','brown_gram')
    def _percent_brown(self):
        for this in self:
            if this.bb_sample_weight != 0:
                brown = this.brown_gram / this.bb_sample_weight  or  0.0000
                this.brown = brown * 100
            else:
                this.brown = 0.0
            return this.brown

    @api.depends('sample_weight','mold_gram')
    def _percent_mold(self):
        for this in self:
            if this.sample_weight != 0:
                mold = this.mold_gram / this.sample_weight  or 0.0000
                this.mold = mold * 100
            else:
                this.mold = 0.0
            return this.mold

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

    @api.depends('sample_weight','screen16_gram')
    def _percent_screen16(self):
        for this in self:
            if this.sample_weight != 0:
                screen16 = this.screen16_gram / this.sample_weight  or 0.0000
                this.screen16 = screen16 * 100
            else:
                this.screen16 = 0.0
            return this.screen16
            
    @api.depends('sample_weight','screen13_gram')
    def _percent_screen13(self):
        for this in self:
            if this.sample_weight > 0 and this.screen13_gram > 0:
                screen13 = this.screen13_gram / this.sample_weight or 0.0000
                this.screen13 = screen13 * 100
            else:
                this.screen13 = 0.0
            return this.screen13
            
    @api.depends('sample_weight','screen19_gram','screen20_gram','screen18_gram','screen16_gram','screen13_gram','belowsc12_gram')
    def _greatersc12_gram(self):
        for this in self:
            if this.sample_weight > 0 and (this.screen20_gram + this.screen19_gram + this.screen18_gram + this.screen16_gram + this.screen13_gram + this.belowsc12_gram) < this.sample_weight:
                this.greatersc12_gram = this.sample_weight - (this.screen20_gram + this.screen19_gram + this.screen18_gram + this.screen16_gram + this.screen13_gram + this.belowsc12_gram)
            else:
                this.greatersc12_gram = 0.0
                
            if this.sample_weight > 0 and (this.screen20_gram + this.screen19_gram + this.screen18_gram + this.screen16_gram + this.screen13_gram + this.belowsc12_gram) == 0:
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
            return this.belowsc12

    @api.depends('sample_weight','burned_gram')
    def _percent_burned(self):
        for this in self:
            if this.sample_weight > 0 and this.burned_gram > 0:
                burned = this.burned_gram / this.sample_weight or 0.0000
                this.burned = burned * 100
            else:
                this.burned = 0.0
            return this.burned

    @api.depends('bb_sample_weight','insect_gram')
    def _percent_insect(self):
        for this in self:
            if this.bb_sample_weight > 0 and this.insect_gram > 0:
                insect = this.insect_gram / this.bb_sample_weight or 0.0000
                this.insect = insect * 100
            else:
                this.insect = 0.0
            return this.insect

    @api.depends('sample_weight','immature_gram')
    def _percent_immature(self):
        for this in self:
            if this.bb_sample_weight != 0:
                immature = this.immature_gram / this.bb_sample_weight  or 0.0000
                this.immature = immature * 100
            return this.immature

    sample_weight = fields.Float(string="Sample Weight", default=0.0000, digits=(12, 2), )
    bb_sample_weight = fields.Float(string="BB Sample Weight", default=0.0000, digits=(12, 2), )
    
    mc_degree = fields.Float(string="MCDegree", default=0.0000, digits=(12, 2), )
    mc = fields.Float(compute='_percent_mc', string="MC_%", readonly=True, store=True, default=0.0000, digits=(12, 2))
    
    fm_gram = fields.Float(string="FM Gram", default=0.0000, digits=(12, 2), )
    fm = fields.Float(compute='_percent_fm',string="FM_%", readonly=True, store=True, default=0.0000, digits=(12, 2),group_operator="avg")
    
    black_gram = fields.Float(string="Black Gram", default=0.0000, digits=(12, 2), )
    black = fields.Float(compute='_percent_black',group_operator="avg",string="Black_%", readonly=True, store=True, default=0.0000, digits=(12, 2))
    
    broken_gram = fields.Float(string="Broken Gram", default=0.0000, digits=(12, 2), )
    broken = fields.Float(compute='_percent_broken',group_operator="avg",string="Broken_%", readonly=True, store=True, default=0.0000, digits=(12, 2))
    
    brown_gram = fields.Float(string="Brown Gram", default=0.0000, digits=(12, 2), ) 
    brown = fields.Float(compute='_percent_brown',group_operator="avg",string="Brown_%", readonly=True, store=True, default=0.0000, digits=(12, 2))
    
    mold_gram = fields.Float(string="Mold Gram", default=0.0000, digits=(12, 2), )
    mold = fields.Float(compute='_percent_mold',group_operator="avg",string="Mold_%", readonly=True, store=True, default=0.0000, digits=(12, 2))
        
    cherry_gram = fields.Float(string="Cherry Gram", default=0.0000, )
    cherry = fields.Float(compute='_percent_cherry', group_operator="avg",string="Cherry_%", readonly=True, store=True, default=0.0000, digits=(12, 2))
    
    excelsa_gram = fields.Float(string="Excelsa Gram", default=0.0000, digits=(12, 2), )
    excelsa = fields.Float(compute='_percent_excelsa', group_operator="avg", string="Excelsa_%", readonly=True, store=True, default=0.0000, digits=(12, 2))
    
    screen20_gram = fields.Float(string="Screen20 Gram", default=0.0000, digits=(12, 2), )
    screen20 = fields.Float(compute='_percent_screen20',group_operator="avg", string="Screen20_%", readonly=True, store=True, default=0.0000, digits=(12, 2))
    
    screen19_gram = fields.Float(string="Screen19 Gram", default=0.0000, digits=(12, 2), )
    screen19 = fields.Float(compute='_percent_screen19',group_operator="avg", string="Screen19_%", readonly=True, store=True, default=0.0000, digits=(12, 2))

    screen18_gram = fields.Float(string="Screen18 Gram", default=0.0000, digits=(12, 2), )
    screen18 = fields.Float(compute='_percent_screen18',group_operator="avg", string="Screen18_%", readonly=True, store=True, default=0.0000, digits=(12, 2))
    
    screen16_gram = fields.Float(string="Screen16 Gram", default=0.0000, digits=(12, 2), )
    screen16 = fields.Float(compute='_percent_screen16',group_operator="avg", string="Screen16 %", readonly=True, store=True, default=0.0000, digits=(12, 2))
    
    screen13_gram = fields.Float(string="Screen13 Gram", default=0.0000, digits=(12, 2), )
    screen13 = fields.Float(compute='_percent_screen13',group_operator="avg", string="Screen13_%", readonly=True, store=True, default=0.0000, digits=(12, 2))
    
    greatersc12_gram = fields.Float(compute='_greatersc12_gram',group_operator="avg", string="Screen12 Gram", readonly=True, store=True, default=0.000, digits=(12, 2))
    greatersc12 = fields.Float(compute='_percent_greatersc12',group_operator="avg", string="Screen12_%", readonly=True, store=True, default=0.000)

    belowsc12_gram = fields.Float(string="Belowsc12 Gram", default=0.000, digits=(12, 2), )
    belowsc12 = fields.Float(compute='_percent_belowsc12',group_operator="avg", string="Belowsc12_%", readonly=True, store=True, default=0.000)
    
    burned_gram = fields.Float(string="Burned Gram", default=0.0000, digits=(12, 2), )
    burned = fields.Float(compute='_percent_burned',group_operator="avg", string="Burned_%", default=0.0000, digits=(12, 2),store=True)
    
    insect_gram = fields.Float(string="Insect Bean Gram", default=0.0000, digits=(12, 2), )
    insect = fields.Float(compute='_percent_insect',group_operator="avg", string="Insect Bean_%", readonly=True, store=True, default=0.0000, digits=(12, 2))
    
    immature_gram = fields.Float(string="Immature Gram", default=0.0000, digits=(12, 2), )
    immature = fields.Float(compute='_percent_immature',group_operator="avg", string="Immature_%", readonly=True, store=True, default=0.0000, digits=(12, 2))

    odor = fields.Char('Odor')

    aprroved_by_quality = fields.Float('Aprroved by Quality',readonly= True)
    date = fields.Datetime('Date', default=datetime.now().strftime(DATETIME_FORMAT),readonly= True)
    picking_ids = fields.One2many('stock.picking','security_gate_id',string = 'Pickings')
    
    date_reject = fields.Datetime('Date Reject',readonly = True)
    product_ids = fields.Many2many('product.product', 'security_gate_product_rel', 'security_gate_id', 'product_id', string='Products',
                                   domain=[('type','in',('consu','product'))],states={'approved': [('readonly', True)]},required = False, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', 
                                 default=lambda self: self.env['res.company']._company_default_get('ned.security.gate.queue'), 
                                 readonly=True, states={'draft': [('readonly', False)]})
    receive_state = fields.Selection(related='picking_ids.state', string='Receive State', store = False)
    
    type_transfer = fields.Selection([("queue", "Queue-Instore"), ("queue-exstore", "Queue-Exstore"),
                                      ('other', 'Other Warehouse'), ("in", "In"), ("out", "Out")], string="Type Transfer")
    link_fot_id = fields.Many2one('stock.picking', string='GRN-FOT No.', )
    districts_id = fields.Many2one('res.district', string='Source of Goods', required=False, states={'approved': [('readonly', True)]}, tracking=True)
    change_warehouse_id = fields.Many2one('stock.warehouse','Change Warehouse',readonly= True,states={'approved': [('readonly', False)]})
    # weighing_app_id = fields.Integer('Weighing App ID', readonly=True)

    product_id_mapping = fields.Many2one('product.product', string='Product', compute='compute_product_mapping', store=True, tracking=True)

    @api.depends('product_ids')
    def compute_product_mapping(self):
        for rec in self:
            if rec.product_ids:
                rec.product_id_mapping = rec.product_ids[0].id

    @api.constrains('product_ids')
    def _check_product_ids(self):
        for record in self:
            if len(record.product_ids) > 1:
                raise UserError(_("You just can choose one product only!!"))

    # Chỉ dùng trong Trường hợp phiếu đã Done
    def btt_change_warehouse(self):
        for sec in self:
            if sec.receive_state =='done' and sec.receive_state == 'approved':
                raise UserError(_('Can not change when transaction has completed!'))
            if sec.change_warehouse_id:
                #Change cho Security Gate
                sec.warehouse_id = sec.change_warehouse_id.id
                #Change for Stock Picking
                for pick in sec.env['stock.picking'].sudo().search([('security_gate_id','=',sec.id)]):                    
                    if pick.security_gate_id:                        
                        pick.env['stock.picking'].sudo().search([('security_gate_id','=',sec.id)]).write({'location_dest_id':sec.change_warehouse_id.lot_stock_id.id,
                                                                                                            'warehouse_id':sec.change_warehouse_id.id})
                        if pick.picking_type_id and pick.picking_type_id.code =='incoming' and pick.picking_type_id.operation == 'factory' and pick.picking_type_id.sequence_id:
                            crop = self.env['ned.crop'].sudo().search([('start_date','<=',datetime.now().date()),('to_date','>=',datetime.now().date())],limit = 1)
                            if crop:
                                name = pick.picking_type_id.sequence_id.next_by_id()
                                pick.name = _(name)[0:len(pick.picking_type_id.sequence_id.prefix)] + '-' + _(crop.short_name) + '.' + _(name)[len(pick.picking_type_id.sequence_id.prefix):len(pick.picking_type_id.sequence_id.prefix)+pick.picking_type_id.sequence_id.padding]
        return    
    
    @api.model
    def create(self, vals):
        """
        Incrementing sequence number for naming document.
        Sequence format are in view.
        """
        code_type=''
        if vals.get('name', 'New') == 'New' and vals.get('type_transfer') in ['queue', 'other']:
            vals['name'] = self.env['ir.sequence'].next_by_code('ned.security.gate.queue.seq') or 'New'
            code_type='incoming'
        
            sql ='''
            SELECT COUNT(id) as total
            FROM ned_security_gate_queue 
            WHERE date(timezone('UTC',create_date::timestamp)) = date(timezone('UTC','%s'::timestamp))
                    AND type_transfer = '%s'
            '''%(datetime.now(),vals.get('type_transfer'))
            self._cr.execute(sql)
            result_sql = self._cr.dictfetchall()
            total_qty_all = result_sql and result_sql[0] and result_sql[0]['total'] or 1
            vals['parking_order'] = total_qty_all

        if vals.get('name', 'New') == 'New' and vals.get('type_transfer') == 'queue-exstore':
            vals['name'] = self.env['ir.sequence'].next_by_code('ned.security.gate.queue.exstore') or 'New'
            code_type='outgoing'
        
        picking_type_id = self.env['stock.picking.type'].search([('code','=',code_type),('operation','=','factory'),('warehouse_id','=',vals['warehouse_id'])])
        if not picking_type_id:
            raise UserError('Picking Type is not set for Delivery Registration, please check again with your warehouse setting')
        vals['picking_type_id'] = picking_type_id and picking_type_id.id or False
        
        result = super(NedSecurityGateQueue, self).create(vals)
        return result
    

    def button_reject(self):
        for this in self:
            this.date_reject = datetime.now()
            this.state = 'reject'
    
    def button_pur_approved(self):
        for this in self:
            date_time_now = datetime.now()
            time_to_reject_the_goods = date_time_now + timedelta(days=date_time_now.hour) - timedelta(days=this.warehouse_id.company_id.time_to_reject_the_goods) 
            sql = '''
                SELECT id 
                FROM ned_security_gate_queue 
                WHERE timezone('UTC',date_reject::timestamp) >= timezone('UTC','%s'::timestamp)
                    AND state ='reject'
                    AND supplier_id =%s
                    AND license_plate ='%s'
            '''%(time_to_reject_the_goods,this.supplier_id.id,this.license_plate)
            self.env.cr.execute(sql)
            if self.env.cr.dictfetchall():
                raise UserError(_('Sorry, registered can not accept.This Vehicle has been rejected.'))
            
            if self.env['purchase.contract'].sudo().search([('partner_id','=',this.supplier_id.id),
                                                            ('state','=','approved'),
                                                            ('qty_unreceived','>',0)]):
                this.button_qc_approved()
            else:
                this.state = 'pur_approved'
            this.arrivial_time= datetime.now()
            
            
        return True
    
    
    def button_qc_approved(self):
        for this in self:
            this.state = 'qc_approved'
            # if this.ligh_burnded_bean_result == 'rejected':
            #     this.state ='reject'
            # else:
            #     this.state = 'qc_approved'

    
    def button_wh_approved(self):
        for this in self:
            this.state = 'wh_approved'
            this.qc_approve_date = datetime.now()
            # if this.ligh_burnded_bean_result == 'rejected':
            #     this.state ='reject'
            # else:
            #     this.state = 'wh_approved'

    
    def button_approve(self):
        # if this.ligh_burnded_bean_result == 'rejected':
        #     this.state ='reject'
        #     return
        if self.env.context.get('default_type_transfer')=='queue': #Nếu là phiếu Đ Ký Nhập hàng
            for this in self:
                this.create_picking()
            self.write({'state': 'approved', 'date_approve': datetime.now()})
            return True
        elif self.env.context.get('default_type_transfer')=='queue-exstore':
            if not self.delivery_id:
                raise UserError(_('Sorry, registered can not approve when DO no. is empty!'))
            else:
                for _do in self.delivery_id:
                    # for this in self:
                    if _do:
                        if _do.type == 'Sale':
                            picking_type_id = 0

                            if _do.contract_id.type != 'local':
                                picking_type_id = self.warehouse_id.out_type_id
                            else:
                                picking_type_id = self.warehouse_id.out_type_local_id

                            if not picking_type_id:
                                raise UserError(_('Need to define Picking Type for this transaction'))

                            if not _do.picking_id:
                                var = {'name': '/',
                                        'picking_type_id': picking_type_id.id or False,
                                        'scheduled_date': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                                        'origin': _do.name,
                                        'partner_id': _do.partner_id.id or False,
                                        'picking_type_code': picking_type_id.code or False,
                                        'location_id': picking_type_id.default_location_src_id.id or False,
                                        'vehicle_no': _do.trucking_no or '',
                                        'trucking_id': self.trucking_id.id or False,
                                        'location_dest_id': picking_type_id.default_location_dest_id.id or False,
                                        'delivery_id': _do.id,
                                        'security_gate_id': self.id,
                                       # 'min_date': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                                       }
                                picking_id = self.env['stock.picking'].create(var)
                                _do.picking_id = picking_id.id

                            else:
                                picking_id = _do.picking_id.update({
                                        'security_gate_id': self.id,
                                        'vehicle_no': _do.trucking_no or '',
                                        'trucking_id': self.trucking_id.id or False,
                                    })

                self.state = 'approved'
                self.product_ids = self.product_id

    def create_picking(self):
        for this in self:
            stock_picking_data = {
                'origin': this.name,
                'warehouse_id': this.warehouse_id.id,
                'partner_id': this.supplier_id.id,
                'vehicle_no': this.license_plate,
                'picking_type_id': this.picking_type_id.id,
                'location_id': this.picking_type_id.default_location_src_id.id or False,
                'location_dest_id': this.warehouse_id.lot_stock_id.id,
                'certificate_id': this.certificate_id.id or False,
                #Kiet: Nghiệp vụ kho ko thấy fields này
                #'estimated_bags': this.estimated_bags or False,
                'security_gate_id': this.id,
                'date_done': datetime.now(),
                'districts_id': this.districts_id.id,
                'backorder_id': this.link_fot_id and this.link_fot_id.id or False,
            }
            self.env['stock.picking'].sudo().create(stock_picking_data)
        return True

    
    def button_cancel(self): 
        if self.picking_ids:
            self.picking_ids.action_cancel()
            self.picking_ids.unlink()
        self.write({'state': 'cancel'})
        return True
    
    
    def print_security_gate(self):
        return self.env['report'].sudo().get_action(self, 'ned_security_gate_queue.report_security_gate')
    

    #####################Report Function ######################## ################################## ################################## ##################################
    def _get_stt(self,o):
        if o and o.picking_ids:
            return '2'
        return '1'
    
    def _get_st(self,o):
        if o and o.picking_ids:
            return '2sn'
        return '1st'
    def _get_grn(self,o):
        if o.picking_ids:
            return ', \n'.join(map(str, [x.name for x in o.picking_ids]))
        else:
            return ''
    
    def get_nasaaa(self, o):
        print('/report/barcode/?barcode_type=%s&amp;value=%s&amp;width=%s&amp;height=%s' % ('Code128', o.name.replace('/', '%2f'), 500, 100))
        return '/report/barcode/?barcode_type=%s&amp;value=%s&amp;width=%s&amp;height=%s' % ('Code128', o.name.replace('/', '%2f'), 500, 100)

    def get_name_report(self):
        return u"Phiếu lấy mẫu (lấy từ xe tải)"
    
    
    def _get_contract(self,o):
        purchase_contract_pool = self.env['purchase.contract']
        name = ''
        for this in o:
            for con in purchase_contract_pool.search([('partner_id','=',this.supplier_id.id),
                                                            ('state','=','approved'),
                                                            ('qty_unreceived','>',0)],limit = 1):
                name += con.name
        return name
    
    def _get_crop(self,o):
        name = 'CROP '
        for this in o:
            cop_pool = self.env['ned.crop']
            for cop in cop_pool.search([('start_date','<=',this.date),('to_date','>=',this.date)],limit = 1):
                name +=cop.name
        return name
    
    
