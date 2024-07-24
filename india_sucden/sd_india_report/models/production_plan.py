# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict
import re
DATE_FORMAT = "%Y-%m-%d"
import datetime, time

from datetime import datetime

class ProductionPlan(models.Model):
    _name = "production.plan"
    _order = 'plan_date desc, id desc'
    
    
    name = fields.Char(string='Name')
    state = fields.Selection([('draft', 'Draft'), ('approve', 'Approve'),('cancel', 'Cancel')], string="State", required=True, default="draft")
    
    from_date = fields.Date(string='SI Date', require=True)
    to_date = fields.Date(string='To Date', required=True, default=datetime.now().date())
    
    product_id = fields.Many2one('product.product', required=True, string='Product',
                                default= lambda r: r.env['product.product'].search([('default_code','=', 'FAQ')]))
    plan_date = fields.Date(string='Plan Date', default=datetime.now().date())
    end_date = fields.Date(string='End Date')

    user_id = fields.Many2one('res.users', string='Create By', default=lambda self: self.env.user)
    user_approve = fields.Many2one('res.users', string='Approved By')

    tons_per_hours = fields.Float(string='Tons Per Hours')
    hours_per_shitf = fields.Float(string='Hours Per Shift')
    total_hours = fields.Float(string='Total Hours', compute='compute_date', digits=(12, 2))
    total_shitf = fields.Float(string='Total Shitf', compute='compute_date', digits=(12, 2))
    total_days = fields.Float(string='Total Days', compute='compute_date', digits=(12, 2))
    
    si_ids = fields.Many2many('shipping.instruction', string="SI", domain=[('contract_id.state','!=','done')])
    stack_ids = fields.Many2many('stock.lot', string="Stack")
    
    detail_si_ids = fields.One2many('production.plan.detail.si','plan_id', string="Detail SI")
    detail_stack_ids = fields.One2many('production.plan.detail.stack','plan_id', string='Detail Stack')
    
    detail_qty_ids = fields.One2many('production.plan.detail.quantity','plan_id', string="Detail Qty")
    
    mc = fields.Float(string='MC', compute='compute_qc', store=True)
    fm = fields.Float(string='Fm', compute='compute_qc', store=True)
    black = fields.Float(string='Back', compute='compute_qc', store=True)
    broken = fields.Float(string='Broken', compute='compute_qc', store=True)
    brown = fields.Float(string='Brown', compute='compute_qc', store=True)
    mold = fields.Float(string='Mold', compute='compute_qc', store=True)
    cherry = fields.Float(string='Cherry', compute='compute_qc', store=True)
    excelsa = fields.Float(string='Excelsa', compute='compute_qc', store=True)
    screen18 = fields.Float(string='Screen18', compute='compute_qc', store=True)
    screen16 = fields.Float(string='Screen16', compute='compute_qc', store=True)
    screen13 = fields.Float(string='Screen13', compute='compute_qc', store=True)
    greatersc12 = fields.Float(string='Screen12', compute='compute_qc', store=True)
    screen12 = fields.Float(string='Below Screen12', compute='compute_qc', store=True)
    immature = fields.Float(string='Immature', compute='compute_qc', store=True)
    burn = fields.Float(string='Burn', compute='compute_qc', store=True)
    eaten = fields.Float('Eaten', compute='compute_qc', store=True)
    total_qty = fields.Float('Total Qty', compute='compute_qc', store=True)
    total_required = fields.Float('Qty Required', default=0.0, compute='compute_qty', store=True)
    total_production = fields.Float('Qty Production', default=0.0, compute='compute_qty', store=True)

    instruction = fields.Text(string='Instruction',
                                default='''- This batch processes FAQ to target products with high MC. Coffee comes out of This batch will be dried and then blend with high MC to have contract MC of each shipment.
- Franchise will be taken at blending batch.
- Scr 13 produce Nestle 7.2, allocate to March and April shipments.
- Scr 16: prioritize to make 58246 of 484 mts.
- Scr 18 will be packed in PP bag, 60 kg/bag, no franchise, no drying. Operations dept. should check quantity of Scr 18 clean from this batch every 2 day for trucking to MBN.''')
    note = fields.Text(string='Note')
    production_id = fields.Many2one('mrp.production', string='Manufacturing Order', domain=[('state','=','in_production')])
    
    @api.onchange('si_ids')
    def onchange_detail_si(self):
        for this in self:
            list_si = []
            list_scr = []
            sql =''
            if this.si_ids:
                for si in this.si_ids:
                    list_si.append((0,0,{'date': si.date,
                                        'month_si': datetime.strptime(si.date,'%Y-%m-%d').strftime("%B")[0:3] + '-' + datetime.strptime(si.date,'%Y-%m-%d').strftime("%Y")[2:4],
                                        'contract_id': si.contract_id.name,
                                        'partner_id': si.partner_id.shortname or si.partner_id.name,
                                        'categ_id': si.shipping_ids.product_id.product_tmpl_id.categ_id.name if si.shipping_ids.product_id.product_tmpl_id.categ_id else False,
                                        'product_id': si.shipping_ids.product_id.default_code,
                                        'description': si.shipping_ids.name,
                                        'product_qty': si.shipping_ids.product_qty,
                                        'packing_id': si.shipping_ids.packing_id.name,
                                        'allowed_franchise': si.contract_id.allowed_franchise,
                                        'plan_id': this.id}))
                
                sql = ('''
                SELECT sum(required_qty) required_qty,
                        src
                FROM (
                        SELECT sum(product_qty) required_qty,
                            pc.name src
                        FROM shipping_instruction_line sil
                            JOIN shipping_instruction si ON si.id = sil.shipping_id
                            JOIN product_product pp on pp.id = sil.product_id
                            JOIN product_template tmpl on pp.product_tmpl_id = tmpl.id
                            JOIN product_category pc on pc.id = tmpl.categ_id
                        WHERE si.id in (%(sid)s)
                        GROUP BY pc.name

                        UNION ALL

                        SELECT 0 required_qty,
                            pc.name src
                        FROM product_category pc
                        WHERE pc.name IN ('G13', 'G16', 'G18')
                    ) scr
                GROUP BY src
                        ''')%({'sid': ' ,'.join(map(str,[x.id for x in this.si_ids]))})
                self._cr.execute(sql)
                for line in self._cr.dictfetchall():
                    list_scr.append((0,0,{
                        'required_qty': line['required_qty'] or '',
                        'categ_id':line['src'] or '',
                        'plan_id': this.id
                            }))
            if list_si != []:
                this.detail_si_ids = list_si
            else:
                this.detail_si_ids = False
            if list_scr != []:
                this.detail_qty_ids = list_scr
            else:
                this.detail_qty_ids = False
                

    @api.onchange('stack_ids')
    def _onchange_stack_ids(self):
        for this in self:
            list_stack = []
            for stack in self.stack_ids:
                list_stack.append((0,0,{'name': stack.name,
                                        'zone_id': stack.zone_id.name,
                                        'product_id': stack.product_id.default_code,
                                        'remaining_qty': stack.remaining_qty,
                                        'mc': stack.mc,
                                        'fm': stack.fm,
                                        'black': stack.black,
                                        'broken': stack.broken,
                                        'brown': stack.brown,
                                        'mold': stack.mold,
                                        'cherry': stack.cherry,
                                        'excelsa': stack.excelsa,
                                        'screen18': stack.screen18,
                                        'screen16': stack.screen16,
                                        'screen13': stack.screen13,
                                        'greatersc12': stack.greatersc12,
                                        'screen12': stack.screen12,
                                        'immature': stack.immature,
                                        'burn': stack.burn,
                                        'eaten': stack.eaten,
                                        'plan_id': this.id
                                }))
            if list_stack != []:
                this.detail_stack_ids = list_stack
            else:
                this.detail_stack_ids = False
                    
    @api.depends('detail_stack_ids','detail_stack_ids.remaining_qty')
    def compute_qc(self):
        for this in self:
            total_qty = screen13 = screen16 = screen18 = mc = fm = black = burn = eaten = 0.0
            broken = brown = mold = cherry = excelsa = greatersc12 = screen12 = immature = 0.0
            if this.detail_stack_ids:
                for stack in this.detail_stack_ids.filtered(lambda x: x.remaining_qty > 0):
                    total_qty += stack.remaining_qty
                    screen13 += stack.screen13*stack.remaining_qty
                    screen16 += stack.screen16*stack.remaining_qty
                    screen18 += stack.screen18*stack.remaining_qty
                    mc += stack.mc*stack.remaining_qty
                    fm += stack.fm*stack.remaining_qty
                    black += stack.black*stack.remaining_qty
                    burn += stack.burn*stack.remaining_qty
                    eaten += stack.eaten*stack.remaining_qty
                    broken += stack.broken*stack.remaining_qty
                    brown += stack.brown*stack.remaining_qty
                    mold += stack.mold*stack.remaining_qty
                    cherry += stack.cherry*stack.remaining_qty
                    excelsa += stack.excelsa*stack.remaining_qty
                    greatersc12 += stack.greatersc12*stack.remaining_qty
                    screen12 += stack.screen12*stack.remaining_qty
                    immature += stack.immature*stack.remaining_qty
                
        this.screen13 = screen13/total_qty if total_qty >0 else 0
        this.screen16 = screen16/total_qty if total_qty >0 else 0
        this.screen18 = screen18/total_qty if total_qty >0 else 0
        this.mc = mc/total_qty if total_qty >0 else 0
        this.fm = fm/total_qty if total_qty >0 else 0
        this.black = black/total_qty if total_qty >0 else 0
        this.burn = burn/total_qty if total_qty >0 else 0
        this.eaten = eaten/total_qty if total_qty >0 else 0
        this.broken = broken/total_qty if total_qty >0 else 0
        this.brown = brown/total_qty if total_qty >0 else 0
        this.mold = mold/total_qty if total_qty >0 else 0
        this.cherry = cherry/total_qty if total_qty >0 else 0
        this.excelsa = excelsa/total_qty if total_qty >0 else 0
        this.greatersc12 = greatersc12/total_qty if total_qty >0 else 0
        this.screen12 = screen12/total_qty if total_qty >0 else 0
        this.immature = immature/total_qty if total_qty >0 else 0
        this.total_qty = total_qty if total_qty > 0 else 0
        
    @api.onchange('screen13','screen16','screen18','total_qty','detail_qty_ids','detail_stack_ids','detail_stack_ids.qty')
    def onchange_qty_production(self):
        for this in self:
            g13 = g16 = g18 = 0.0
            if this.detail_stack_ids:
                for line in this.detail_stack_ids.filtered(lambda x: x.remaining_qty > 0):
                    g13 += (line.screen13 * line.remaining_qty)/100
                    g16 += (line.screen16 * line.remaining_qty)/100
                    g18 += (line.screen18 * line.remaining_qty)/100
            if this.detail_qty_ids:
                for line in this.detail_qty_ids:
                    if line.categ_id == 'G13':
                        line.update({'recovery': this.screen13,
                                    'qty': g13})
                    if line.categ_id == 'G16':
                        line.update({'recovery': this.screen16,
                                    'qty': g16})
                    if line.categ_id == 'G18':
                        line.update({'recovery': this.screen18,
                                    'qty': g18})
    
    @api.depends('detail_qty_ids')
    def compute_qty(self):
        for this in self:
            total_required = total_production = 0.0
            if this.detail_qty_ids:
                total_required = sum([x.required_qty for x in this.detail_qty_ids])
                total_production = sum([x.qty for x in this.detail_qty_ids])
        this.total_required = total_required or 0
        this.total_production = total_production or 0
        
    @api.depends('tons_per_hours','hours_per_shitf','total_qty')
    def compute_date(self):
        for this in self:
            total_hours = total_shitf = total_days = 0.0
            if this.tons_per_hours > 0 and this.total_qty > 0:
                total_hours = this.total_qty/this.tons_per_hours/1000
                if this.hours_per_shitf > 0:
                    total_shitf = total_hours/this.hours_per_shitf
                    total_days = total_shitf/2
            this.update({
                    'total_hours': total_hours,
                    'total_shitf': total_shitf,
                    'total_days': total_days
            })

    def action_approve(self):
        for this in self:
            mess = ''
            for line in this.detail_qty_ids:
                if line.required_qty > line.qty:
                    mess += _('%s: required %s but production plan only %s.\n')%(line.categ_id, line.required_qty, line.qty)
            if not this.end_date:
                mess += _('Please set end date plan.')

            if mess != '':
                raise UserError(mess)
            else:
                return self.write({'state': 'approve',
                                    'user_approve': self.env.user.id})
    
    @api.model
    def create(self,vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('production.plan') or '/'
        return super(ProductionPlan, self).create(vals)
    
    def print_plan(self):
        return {'type': 'ir.actions.report.xml','report_name':'report_production_plan'}
    
    def print_plan_pdf(self):
        return {'type': 'ir.actions.report.xml','report_name':'report_production_plan_pdf'}

class ProductionPlanDetaiSI(models.Model):
    _name = 'production.plan.detail.si'
    
    date = fields.Date(string='Date')
    month_si = fields.Char(string='Month')
    contract_id = fields.Char(string='SI Number')
    partner_id = fields.Char(string='Counter Party')
    
    categ_id = fields.Char(string='Grade')
    product_id = fields.Char(string='Product')
    
    description = fields.Char(string="Quality Detail")
    
    product_qty = fields.Float(string='Quantity')
    allowed_franchise = fields.Float(string='Franchise')
    
    packing_id = fields.Char(string='Packing')
    
    plan_id = fields.Many2one('production.plan')
    

class ProductionPlanDetaiStack(models.Model):
    _name = 'production.plan.detail.stack'
    
    zone_id = fields.Char(string='Zone')
    name = fields.Char(string='Stack')
    
    
    product_id = fields.Char(string='Product')
    
    remaining_qty = fields.Float(string='Basis Weight')
    
    mc = fields.Float(string='MC')
    fm = fields.Float(string='Fm')
    black = fields.Float(string='Back')
    broken = fields.Float(string='Broken')
    brown = fields.Float(string='Brown')
    mold = fields.Float(string='Mold')
    cherry = fields.Float(string='Cherry')
    excelsa = fields.Float(string='Excelsa')
    screen18 = fields.Float(string='Screen18')
    screen16 = fields.Float(string='Screen16')
    screen13 = fields.Float(string='Screen13')
    greatersc12 = fields.Float(string='Screen12')
    screen12 = fields.Float(string='Below Screen12')
    immature = fields.Float(string='Immature')
    burn = fields.Float(string='Burn')
    eaten = fields.Float('Eaten')
    
    plan_id = fields.Many2one('production.plan')
    
    
class ProductionPlanDetaiQuantity(models.Model):
    _name = 'production.plan.detail.quantity'
    
    
    categ_id = fields.Char(string='Scr')
    
    required_qty = fields.Float(string="Required")
    
    recovery = fields.Float(string='Recovery')
    
    qty = fields.Float(string='Quantity')
    
    plan_id = fields.Many2one('production.plan')
    
    
    
    
