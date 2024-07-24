# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from bisect import bisect_left
from collections import defaultdict
import re
from time import gmtime, strftime
DATE_FORMAT = "%Y-%m-%d"
import base64, xlrd
import time

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

class ProductionAnalysis(models.Model):
    _name = "production.analysis"
    _order = 'production_id desc'
    
    def export_data_pnl_upgrade(self):
        return self.env.ref(
                'sd_report.batch_report_pnl_upgrade').report_action(self)
                
    
    def export_data_pnl_bta(self):
        return self.env.ref(
                'sd_report.batch_report_pnl_bta').report_action(self)
    
    @api.model
    def _domain_production(self):
        prod = []
        where = '1 = 1'
        if self._context.get('normal', False):
            where += "AND name ilike 'BTA%'"
        if self._context.get('upgrade', False):
            where += "AND name not like 'BTA%'"

        sql = '''
            SELECT id
            FROM mrp_production
            WHERE %s
        '''%(where)
        self.env.cr.execute(sql)
        for pro in self.env.cr.dictfetchall():
            prod.append(pro['id'])     

        if len(prod) == 0:
            return [('id','=',False)]
        
        if len(prod) == 1:
            return [('id','=',int(prod[0]))]            
        else:              
            return [('id','in',tuple(prod))]
        
    @api.model
    def load_all_pnl(self):
        for this in self.env['mrp.production'].search([('state','=','done'),('report_pnl','=',False)],limit = 10):
            type ='normal'
            if this.name[0:3] != 'BTA':
                type = 'upgrade'
            analysis_ids = self.env['production.analysis'].search([('production_id','=',this.id)])
            if analysis_ids:
                this.report_pnl =True
                continue
            else:
                analysis = self.env['production.analysis'].create({'production_id':this.id,'type':type})
                if type =='normal':
                    analysis.load_data()
                else:
                    analysis.load_data_upgrade()
            this.report_pnl =True

            
    def compute_p_average_percent_discount(self):
        for record in self:
            total_value_input = sum(i.sale_to_ams * i.qty_allocation for i in record.input_value_ids)
            sum_payment_weight = sum(i.qty_allocation for i in record.input_value_ids)
            if sum_payment_weight > 0:
                record.p_average = total_value_input / sum_payment_weight
            else:
                record.p_average = 0

            total_value_from_low_grade = sum(i.value_low_grade * i.net_qty for i in record.output_ids.filtered(
                lambda x: x.exportale == 'n' and x.product_id.default_code not in ['HUSKS', 'STONES', 'PCR', 'Dust',
                                                                                   'WP Dust']))
            total_net_qty = sum(i.net_qty for i in record.output_ids.filtered(
                lambda x: x.exportale == 'n' and x.product_id.default_code not in ['HUSKS', 'STONES', 'PCR', 'Dust',
                                                                                   'WP Dust']))
            if total_net_qty > 0:
                record.percent_discount = (1 - (total_value_from_low_grade / total_net_qty)) * 100
            else:
                record.percent_discount = 0

    p_average = fields.Float(string='P Average', compute='compute_p_average_percent_discount')
    percent_discount = fields.Float(string='% discount', compute='compute_p_average_percent_discount')
    ra_input = fields.Float(string='RA')
    note_fail = fields.Char(string='Log Note')
    sml_quantity = fields.Float(string='SML/SPL Quantity')
    sml_value = fields.Float(string='SML/SPL Value')
    
    input_upgrade_ids = fields.One2many('production.analysis.line.input.quantity','analysis_upgrade_id', string="Inputs")

    production_id = fields.Many2one('mrp.production',string="Production", domain=_domain_production)
    type_production = fields.Char(string='Type', related='production_id.bom_id.master_code_id.type_code', store=True)
    warehouse_id = fields.Many2one('stock.warehouse',string="Warehouse", related='production_id.warehouse_id', store = True)
    production_state = fields.Selection(related='production_id.state',string ='Production Status',store =True,readonly =True)
    name = fields.Char(string="Name", default=lambda self: _('New'))

    type = fields.Selection([('normal','Normal'),
                            ('upgrade','Upgrade')],string='Type')
    
    input_ids = fields.One2many('production.analysis.line.input.quantity','analysis_id', string="Inputs")
    input_value_ids = fields.One2many('production.analysis.line.input.value','analysis_id', string="Inputs")
    output_ids = fields.One2many('production.analysis.line.output','analysis_id', string="Oututs")

    daily_confirmation_ids = fields.One2many('production.analysis.line.daily.confirmation', 'analysis_id', string='Daily Confirmation')

    daily_ids = fields.Many2many('daily.confirmation', string='Daily Confirmation')
    failure = fields.Integer('Error(s)', default=0, copy=False)
    warning_mess = fields.Text('Message', copy=False)

    crop_id = fields.Many2one('ned.crop', string='Crop', required=True, default=lambda self: self.env['ned.crop'].search([('state', '=', 'current')], limit=1))

    liffe = fields.Float(string='LIFFE')
    diff = fields.Float(string='DIFF')
    cost_price = fields.Float(string='Cost Price')
    exchange_rate = fields.Float(string='Exchange Rate', digits=(12,0))
    week = fields.Integer('Week')
    notes = fields.Text(related ='production_id.notes',string='Notes',readonly = True,store= True)
    premium_utz = fields.Float(string='UTZ', digits=(12,0))
    premium_4c = fields.Float(string='4C', digits=(12,0))
    trucking_cost = fields.Float(string='Trucking Cost', digits=(12,0))
    

    @api.depends('output_ids.real_qty', 'input_value_ids.qty_allocation', 'input_value_ids.payment',
                 'input_ids.real_qty', 'input_upgrade_ids.real_qty', 'input_upgrade_ids.value_input', 'sml_value')
    def _comput_input_quantity(self):
        input_quantity = 0.0
        input_value = 0.0
        payment_weight = 0.0
        output_quantity = 0.0
        for this in self:
            input_quantity = sum([x.real_qty for x in this.input_ids]) if this.input_ids else sum(
                [x.real_qty for x in this.input_upgrade_ids])
            input_value = sum([x.payment for x in this.input_value_ids]) if this.input_value_ids else sum(
                [x.value_input for x in this.input_upgrade_ids])
            payment_weight = sum([x.qty_allocation for x in this.input_value_ids])
            output_quantity = sum([x.real_qty for x in this.output_ids])
        self.input_quantity = input_quantity
        self.input_value = input_value + self.sml_value
        self.payment_weight = payment_weight
        self.output_quantity = output_quantity


    input_quantity = fields.Float(string='Input Quantity', compute='_comput_input_quantity',store=True, digits=(12,0))
    input_value = fields.Float(string='Input Value', compute='_comput_input_quantity',store=True, digits=(12,0))

    @api.depends('output_ids.value_output')
    def _compute_output(self):
        output_value = 0.0
        for this in self:
            output_value = sum([x.value_output for x in this.output_ids])
        self.output_value = output_value

    output_quantity = fields.Float(string='Output Quantity', compute='_comput_input_quantity',store=True, digits=(12,0))
    output_value = fields.Float(string='Output Value', compute='_compute_output',store=True, digits=(12,0))

    payment_weight = fields.Float(string='Payment Weight', compute='_comput_input_quantity',store=True, digits=(12,0))

    @api.depends('input_value_ids.premium_total','input_value_ids.qty_allocation','input_value_ids.subsidy')
    def _comput_premium(self):
        for this in self:
            total_subsidy = 0.0
            total_pre =  0.0
            total_qty = sum([x.qty_allocation for x in this.input_value_ids])
            for pre in this.input_value_ids:
                total_pre += pre.premium_total*pre.qty_allocation
                total_subsidy += pre.subsidy *pre.qty_allocation
            this.premium = total_subsidy/total_qty if total_qty >0 else 0.0
            this.premium_total = total_pre/total_qty if total_qty >0 else 0.0

    premium = fields.Float(string='Subsidy', compute='_comput_premium',store=True)
    premium_total = fields.Float(string='Cross Check', compute='_comput_premium',store=True)

    @api.depends('output_value','input_value','output_quantity','cost_price','premium')
    def _compute_pnl(self):
        pnl = 0.0
        pnl_per_ton = 0.0
        for this in self:
            if this.type == 'upgrade':
                pnl = this.output_value - this.input_value
                pnl_per_ton = pnl/this.output_quantity*1000 if this.output_quantity > 0 else 0
            else:
                pnl = this.output_value - this.input_value - (this.cost_price*this.output_quantity/1000)
                pnl_per_ton = pnl/this.payment_weight*1000 if this.payment_weight >0 else 0.0
            this.total_pnl = pnl
            this.pnl_per_ton = pnl_per_ton
            if this.type == 'upgrade':
                this.real_extraction = pnl/this.payment_weight*1000 + this.premium if this.payment_weight >0 else 0.0
            else:
                this.real_extraction = this.premium + pnl_per_ton if this.payment_weight >0 else 0.0

    total_pnl = fields.Float(string='Total PnL', compute='_compute_pnl',store=True, digits=(12,0))
    pnl_per_ton = fields.Float(string='PnL per ton', compute='_compute_pnl',store=True, digits=(12,0))

    real_extraction = fields.Float(string='Real Extraction', compute='_compute_pnl',store=True)

    price_premium = fields.Float(string='Price Premium')
    sale_to_ams = fields.Float(string='Sale to Ams')

    @api.model
    def create(self,vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['mrp.production'].search([('id','=',vals['production_id'])]).name
        return super(ProductionAnalysis, self).create(vals)

    
    def compute_price_premium(self):
        total_pre_price = total_sale = 0.0
        total_qty = 0.0
        for this in self:
            total_qty = sum([x.qty_allocation for x in this.input_value_ids])
            for pre in this.input_value_ids:
                total_pre_price += pre.factory_price_premium * pre.qty_allocation
                total_sale += pre.sale_to_ams*pre.qty_allocation
        self.price_premium = total_pre_price/total_qty if total_qty >0 else 0.0
        self.sale_to_ams = total_sale/total_qty if total_qty >0 else 0.0

    def load_liffe_diff(self):
        val = {}
        for this in self:
            if this.daily_ids:
                    sql = ('''
                        SELECT liffe, diff, cost_price, exchange_rate 
                        FROM daily_confirmation
                        WHERE date_create = (
                            SELECT max(date_create) 
                            FROM daily_confirmation 
                            where id in (%(sid)s))''')%({'sid': ' ,'.join(map(str, [x.id for x in this.daily_ids]))})
                    self.env.cr.execute(sql)
                    for line in self.env.cr.dictfetchall():
                        val={
                            'liffe': line['liffe'] or 0.0,
                            'diff': line['diff'] or 0.0,
                            'cost_price': line['cost_price'] or 0.0,
                            'exchange_rate': line['exchange_rate'] or 0.0
                        }
            this.update(val)
    
    

    @api.model
    def _load_data(self):
        for this in self:
            sql ='''
                DELETE FROM production_analysis_line_input_quantity where analysis_id = %s or analysis_upgrade_id = %s;
                DELETE FROM production_analysis_line_input_value where analysis_id = %s ;
                DELETE FROM production_analysis_line_output where analysis_id = %s ;
                
                SELECT spt.code as picking_type_code,
                        sp.id,
                        sml.lot_id as stack_id,
                        DATE(timezone('UTC', sp.date_done::timestamp)) date_done
                FROM stock_picking sp join stock_move_line sml on sp.id = sml.picking_id
                    join stock_picking_type spt on sp.picking_type_id = spt.id
                WHERE (sml.finished_id = %s or sml.material_id = %s)
                    AND spt.code in ('production_in','production_out')
                    AND (total_qty !=0 OR total_init_qty !=0)
                    AND sp.state ='done'
                
            '''%(this.id, this.id, this.id, this.id, this.production_id.id, this.production_id.id)
            self.env.cr.execute(sql)
            for line in self.env.cr.dictfetchall():
                val ={
                    'stack_id':line['stack_id'],
                    'picking_id':line['id'],
                    'date': line['date_done'],
                    }
                if line['picking_type_code'] == 'production_out':
                    new_id = self.env['production.analysis.line.input.quantity'].create(val)
                    if this.type == 'upgrade':
                        new_id.update({'analysis_upgrade_id': this.id,
                                        'production_id':this.production_id.id})
                    else:
                        new_id.update({'analysis_id': this.id})
                else:
                    picking_id = self.env['stock.picking'].search([('id','=',line['id'])])
                    if picking_id.categ_id.code != 'Loss':
                        val.update({'product_id':picking_id.move_line_ids_without_package[0].product_id.id,
                                   'categ_id':picking_id.move_line_ids_without_package[0].product_id.categ_id.id,}) 
                        new_id = self.env['production.analysis.line.output'].create(val)
                        new_id.update({'analysis_id': this.id})
        return True

    
    def load_data(self):
        res_user = self.env['res.users']
        for this in self:
            self._load_data()
            self.create_input_value()
            self.action_load_daily_confirmation()
            if this.liffe == 0.0 and this.diff == 0.0 and this.exchange_rate == 0.0 and this.cost_price == 0.0:
                self.load_liffe_diff()
            self.action_allocation_price()
            self.update_allocation_price()
            self.compute_price_premium()
            if this.production_id and this.production_id.date_planned_start:
                this.week = res_user._convert_user_datetime(this.production_id.date_planned_start).strftime("%U")
        return True

    
    def load_data_upgrade(self):
        res_user = self.env['res.users']
        for this in self:
            self._load_data()
            if this.production_id and this.production_id.date_planned_start:
                this.week = res_user._convert_user_datetime(this.production_id.date_planned_start).strftime("%U")
            if this.production_id:
                date_planned = this.production_id.date_planned_start
                crop = self.env['ned.crop'].sudo().search([('start_date','<=',date_planned.date()),('to_date','>=',date_planned.date())],limit = 1)
                if crop:
                    sql='''
                        SELECT SUM(dcl.liffe*dcl.qty)/SUM(dcl.qty) liffe,
                               SUM(dcl.diff*dcl.qty)/SUM(dcl.qty) diff
                        FROM daily_confirmation_line dcl
                            JOIN purchase_contract pc ON pc.id = dcl.contract_id
                        WHERE pc.crop_id = %s
                    '''%(crop.id)
                    self.env.cr.execute(sql)
                    for line in self.env.cr.dictfetchall():
                        this.liffe =line['liffe']
                        this.diff =line['diff']
                    if not this.liffe and not this.diff:
                        sql='''
                            SELECT SUM(dcl.liffe*dcl.qty)/SUM(dcl.qty) liffe,
                                SUM(dcl.diff*dcl.qty)/SUM(dcl.qty) diff
                            FROM daily_confirmation_line dcl
                                JOIN purchase_contract pc ON pc.id = dcl.contract_id
                            WHERE pc.crop_id = %s ''' % (crop.id - 1)
                        self.env.cr.execute(sql)
                        for line in self.env.cr.dictfetchall():
                            this.liffe =line['liffe']
                            this.diff =line['diff']
        return True
    

    @api.model
    def _prepare_input_value(self, allocation_ids, picking_id, stack_id, this):
        val = {}
        for allocate in allocation_ids:
            if not allocate.contract_id.npe_ids:
                val = {
                    'contract_id': allocate.contract_id.id or False,
                    'contract_price': allocate.contract_id.relation_price_unit or 0.0,
                    'qty_allocation': allocate.qty_allocation or 0.0,
                    'stack_id': stack_id.id,
                    'picking_id': picking_id.id,
                    'premium': this.premium_utz if allocate.contract_id.certificate_id.code == 'UTZ' else this.premium_4c if allocate.contract_id.certificate_id.code in ['4C', '4C FC'] else this.ra_input if allocate.contract_id.certificate_id.code == 'RA' else 0,
                    'trucking_cost': picking_id.cost or 0.0,
                    'analysis_id': this.id
                }
            else:
                avg_price = 0.0
                total_qty = 0.0
                total_price = 0.0
                for npe in allocate.contract_id.npe_ids:
                    total_qty += npe.product_qty
                    total_price += (npe.product_qty * npe.contract_id.relation_price_unit)
                avg_price = total_price / total_qty
                for npe in allocate.contract_id.npe_ids:
                    if npe.contract_id.type == 'purchase':
                        avg_price = npe.contract_id.relation_price_unit
                    val = {
                        'contract_id': npe.contract_id.id or False,
                        'source_contract_id': allocate.contract_id.id or False,
                        'contract_price': avg_price or 0.0,
                        'qty_allocation': allocate.qty_allocation or 0.0,
                        'stack_id': stack_id.id,
                        'picking_id': picking_id.id,
                        'premium': this.premium_utz if allocate.contract_id.certificate_id.code == 'UTZ' else this.premium_4c if allocate.contract_id.certificate_id.code in ['4C', '4C FC'] else this.ra_input if allocate.contract_id.certificate_id.code == 'RA' else 0,
                        'trucking_cost': picking_id.cost or 0.0,
                        'analysis_id': this.id
                    }
            self.env['production.analysis.line.input.value'].create(val)

    
    def create_input_value(self):
        for this in self:
            if this.input_ids:
                sql = '''
                SELECT stack_id
                FROM (
                    SELECT stack_id
                    FROM production_analysis_line_input_quantity
                    WHERE analysis_id = %s
                    GROUP BY stack_id

                    UNION ALL

                    SELECT stack_id
                    FROM stock_move_line sm
                    WHERE picking_id IN (
                        SELECT backorder_id 
                        FROM stock_picking sp
		                WHERE sp.id IN  (
                            SELECT picking_id
                            FROM stock_move sm 
                            JOIN (
                                SELECT stack_id
                                FROM production_analysis_line_input_quantity
                                WHERE analysis_id = %s
                                GROUP BY stack_id
                                ) st ON st.stack_id = sm.stack_id
                            JOIN stock_picking sp ON sp.id = sm.picking_id
                            WHERE sp.picking_type_code = 'incoming' or sp.picking_type_code = 'transfer_in'
                            )
                        )
                        AND stack_id is not null
                    GROUP BY stack_id
                    ) st
                GROUP BY stack_id
                    '''%(this.id,this.id)
                print(sql)
                self._cr.execute(sql)
                for line in self._cr.dictfetchall():
                    stack_id = self.env['stock.lot'].search([('id','=', line['stack_id'])])
                    val = {}
                    for move in stack_id.move_line_ids.filtered(lambda x: x.picking_id.picking_type_id.code == 'incoming' or x.picking_id.picking_type_id.code == 'transfer_in'):
                        allocation_ids = self.env['stock.allocation'].search([('picking_id','=', move.picking_id.id)])
                        if allocation_ids:
                            self._prepare_input_value(allocation_ids, move.picking_id, stack_id, this)
                        else:
                            if move.picking_id.backorder_id:
                                allocation_ids = self.env['stock.allocation'].search([('picking_id','=', move.picking_id.backorder_id.id)])
                                if allocation_ids:
                                    self._prepare_input_value(allocation_ids, move.picking_id.backorder_id, stack_id, this)
                                # for allocate in allocation_ids:
                                #     val = {
                                #         'contract_id': allocate.contract_id.id or False,
                                #         'contract_price': allocate.contract_id.price_unit if allocate.contract_id.type == 'purchase' else 0.0,
                                #         'qty_allocation': allocate.qty_allocation or 0.0,
                                #         'stack_id': stack_id.id,
                                #         'picking_id': move.picking_id.backorder_id.id,
                                #         'premium': 300 if allocate.contract_id.certificate_id.code == 'UTZ' else 200 if allocate.contract_id.certificate_id.code == '4C' else 0.0,
                                #         'trucking_cost': 270 if move.picking_id.backorder_id.name[4:6] == 'GL' else 0.0,
                                #         'analysis_id':this.id
                                #     }
                                    # self.env['production.analysis.line.input.value'].create(val)
        return True


    
    def action_load_daily_confirmation(self):
        for this in self:
            if not this.input_value_ids:
                return
            else:
                nvp_ids = self.env['purchase.contract']
                nvp_ids |= this.input_value_ids.mapped('contract_id')
                nvp_ids |= this.input_value_ids.mapped('source_contract_id').mapped('npe_ids').mapped('contract_id')
                daily_confirmtion_ids = self.env['daily.confirmation.line'].search([('contract_id','in', nvp_ids.ids)]).mapped('daily_id')
                this.daily_ids = daily_confirmtion_ids.ids
                daily_confirmtion_line_ids = self.env['daily.confirmation.line'].search([('daily_id','in', daily_confirmtion_ids.ids)])
                daily_comfirmation_list = []
                existed_list = []
                if daily_confirmtion_ids:
                    self.env.cr.execute('''
                        BEGIN;
                            DELETE FROM production_analysis_line_daily_confirmation where analysis_id = %s;
                        COMMIT;'''%(this.id))
                    for line in daily_confirmtion_line_ids:
                        if line.contract_id.id not in existed_list:
                            existed_list.append(line.contract_id.id)
                            if len([x.contract_id for x in daily_confirmtion_line_ids if x.contract_id.id == line.contract_id.id]) == 1:
                                daily_comfirmation_list.append((0,0,{
                                        'contract_id': line.contract_id.id,
                                        'liffe': line.liffe,
                                        'diff': line.diff,
                                        'diff_price': line.diff_price,
                                        'exchange_rate': line.exchange_rate,
                                        'analysis_id': this.id
                                    }))
                            elif len([x.contract_id for x in daily_confirmtion_line_ids if x.contract_id.id == line.contract_id.id]) > 1:
                                total_qty = 0.0
                                new_vals = self.env['daily.confirmation.line'].search([('contract_id','=',line.contract_id.id),('daily_id','in',daily_confirmtion_ids.ids)],limit=1, order='create_date DESC')
                                diff_price = new_vals.diff_price
#self.env['daily.confirmation.line'].search([('contract_id','=',line.contract_id.id),('daily_id','in',daily_confirmtion_ids.ids)],limit=1, order='create_date DESC').diff_price
                                total_qty = sum([x.qty for x in daily_confirmtion_line_ids.filtered(lambda x: x.contract_id.id == line.contract_id.id)])
                                toal_liffe = total_diff = total_exchange = 0.0
                                newdiff = new_vals.diff
                                new_exchange =  new_vals.exchange_rate
                                for x in daily_confirmtion_line_ids.filtered(lambda x: x.contract_id.id == line.contract_id.id):
                                    total_diff += x.diff*x.qty if x.qty > 0 else x.diff
                                    total_exchange += x.exchange_rate*x.qty  if x.qty > 0 else x.exchange_rate
                                    toal_liffe += x.liffe*x.qty  if x.qty > 0 else x.liffe
                                daily_comfirmation_list.append((0,0,{
                                        'contract_id': line.contract_id.id,
                                        'liffe': toal_liffe/total_qty if total_qty > 0 else 0.0,
                                        'diff': newdiff, #total_diff/total_qty if total_qty > 0 else 0.0,
                                        'exchange_rate': new_exchange, #total_exchange/total_qty if total_qty > 0 else 0.0,
                                        'analysis_id': this.id,
                                        'diff_price': diff_price or 0.0,
                                    }))
                if daily_comfirmation_list != []:
                    this.daily_confirmation_ids = daily_comfirmation_list
                else:
                    this.daily_confirmation_ids = False

        nvp_ids = self.env['purchase.contract']
        nvp_ids |= self.input_value_ids.mapped('source_contract_id').mapped('npe_ids').mapped('contract_id')
        for nvp in nvp_ids:
            if not self.daily_confirmation_ids.filtered(lambda x: x.contract_id == nvp):
                self.env['production.analysis.line.daily.confirmation'].create({'contract_id': nvp.id,
                                                                                'liffe': self.liffe,
                                                                                'diff': self.diff,
                                                                                'exchange_rate': self.exchange_rate,
                                                                                'analysis_id': self.id})

        return True


    
    def action_allocation_price(self):
        for this in self:
            if this.input_value_ids and this.daily_confirmation_ids:
                for npe in this.input_value_ids.mapped('source_contract_id'):
                    nvp_ids = npe.npe_ids.mapped('contract_id')
                    nvp_confirm_ids = this.daily_confirmation_ids.filtered(lambda x: x.contract_id.id in nvp_ids.ids)
                    total_liffe = total_qty = total_diff = total_exchange =  0.0
                    avg_liffe = avg_diff = avg_exchange = 0.0

                    for nvp in nvp_confirm_ids:
                        qty = npe.npe_ids.filtered(lambda x: x.contract_id.id == nvp.contract_id.id).product_qty
                        total_diff += nvp.diff*qty
                        total_liffe += nvp.liffe*qty
                        total_exchange += nvp.exchange_rate*qty
                        total_qty += qty
                    avg_diff = total_qty != 0 and total_diff/total_qty
                    avg_exchange = total_qty != 0 and total_exchange/total_qty
                    avg_liffe = total_qty != 0 and total_liffe/total_qty

                    for inv in this.input_value_ids.filtered(lambda x: x.source_contract_id.id == npe.id):
                        if avg_exchange == 0:
                            avg_exchange = this.exchange_rate
                        inv.update({
                            'diff': avg_diff,
                            'liffe': avg_liffe,
                            'exchange_rate': avg_exchange,
                            'diff_price':inv.contract_id.diff_price,
                            'subsidy':inv.contract_id and inv.contract_id.contract_line and inv.contract_id.contract_line[0].premium or 0.0,
                        })
                for nvp in this.input_value_ids.filtered(lambda x: x.contract_id.type == 'purchase'):
                    daily_confirmation_id = this.daily_confirmation_ids.filtered(lambda x: x.contract_id.id == nvp.contract_id.id)
                    nvp.update({
                            'diff': daily_confirmation_id.diff,
                            'liffe': daily_confirmation_id.liffe,
                            'exchange_rate': daily_confirmation_id.exchange_rate,
                            'subsidy':nvp.contract_id and nvp.contract_id.contract_line and nvp.contract_id.contract_line[0].premium or 0.0,
                        })
                for npe in this.input_value_ids.filtered(lambda x: not x.source_contract_id and x.contract_id.type == 'consign'):
                    npe.update({
                            'diff': this.diff,
                            'liffe': this.liffe,
                            'exchange_rate': this.exchange_rate,
                            'subsidy':npe.contract_id and npe.contract_id.contract_line and npe.contract_id.contract_line[0].premium or 0.0,
                        })
                for ptbf in this.input_value_ids.filtered(lambda x: not x.source_contract_id and x.contract_id.type == 'ptbf'):
                    daily_confirmation_id = this.daily_confirmation_ids.filtered(lambda x: x.contract_id.id == ptbf.contract_id.id)
                    liffe = daily_confirmation_id.liffe
                    if liffe == 0:
                        liffe = this.liffe
                    ptbf.update({
                            'diff': daily_confirmation_id.diff,
                            'liffe': liffe,
                            'exchange_rate': this.exchange_rate,
#                             'diff_price':ptbf.contract_id.diff_price,
                            'subsidy':ptbf.contract_id and ptbf.contract_id.contract_line and ptbf.contract_id.contract_line[0].premium or 0.0,
                        })
                for ptbf in this.input_value_ids.filtered(lambda x: x.liffe == 0 and x.contract_id.type == 'ptbf'):
                    ptbf.update({'liffe':this.liffe})
                    
                for npe in this.input_value_ids.filtered(lambda x: x.contract_id.type == 'consign'):
                    npe.update({
                            'diff': this.cost_price,
                        })
                for input_line in this.input_value_ids.filtered(lambda x: not x.diff_price != 0.0) :
                    daily_confirmation_id = this.daily_confirmation_ids.filtered(lambda x: x.contract_id.id == input_line.contract_id.id and x.diff_price != 0.0)
                    input_line.update({
                            'diff_price': daily_confirmation_id.diff_price,
                        })
        return

    
    def update_allocation_price(self):
        for this in self:
            for contract in this.input_value_ids.filtered(lambda x: x.diff == 0 and x.liffe == 0 and x.exchange_rate == 0):
                contract.update({
                        'diff': contract.diff == 0.0 and this.diff,
                        'liffe': contract.liffe == 0.0 and this.liffe,
                        'exchange_rate': contract.exchange_rate == 0.0 and this.exchange_rate
                    })
        return

class ProductionAnalysisLineInputQuantity(models.Model):
    _name = "production.analysis.line.input.quantity"
    _order = 'date, id asc'


    @api.depends('picking_id')
    def compute_qc(self):
        for this in self:
            if this.picking_id:
                for move in this.picking_id.move_line_ids_without_package.filtered(lambda r: r.product_id.id == this.product_id.id):
                    this.update({
                        'bag_no': move.bag_no,
                        'packing_id': move.packing_id,
                        'net_qty': move.init_qty,
                        'real_qty': move.init_qty
                    })
                for kcs in this.picking_id.kcs_line.filtered(lambda r: r.product_id.id == this.product_id.id):
                    this.update({
                        'mc': kcs.mc,
                        'fm': kcs.fm,
                        'black': kcs.black,
                        'broken': kcs.broken,
                        'brown': kcs.brown,
                        'mold': kcs.mold,
                        'cherry': kcs.cherry,
                        'excelsa': kcs.excelsa,
                        'screen18': kcs.screen18,
                        'screen16': kcs.screen16,
                        'screen13': kcs.screen13,
                        'screen12': kcs.belowsc12,
                        'greatersc12': kcs.greatersc12,
                        'burn': kcs.burned,
                        'eaten': kcs.eaten,
                        'stone_count': kcs.stone_count,
                        'stick_count': kcs.stick_count,
                        'immature': kcs.immature,
                    })
    
    analysis_id = fields.Many2one('production.analysis',string="Report")

    stack_id = fields.Many2one('stock.lot',string="Stack No.")

    picking_id = fields.Many2one('stock.picking',string="Picking")
    production_id = fields.Many2one('mrp.production',related='analysis_id.production_id',string="Batch No.", store=True)
    product_id = fields.Many2one('product.product',string="Product.",related='stack_id.product_id', store=True)
    
    zone_id = fields.Many2one('stock.zone',string='Zone', related='stack_id.zone_id', store=True)



    state = fields.Selection(related='picking_id.state', string='State')
    
    date = fields.Date(string='Date')
    
    #########################
    net_qty = fields.Float(compute='compute_qc', store=True, string="Net Weight", digits=(12, 0))
    real_qty = fields.Float(compute='compute_qc', store=True, string="Real Weight", digits=(12, 0))

    bag_no = fields.Float(string='Bag No', compute='compute_qc', store=True, digits=(12, 0))
    packing_id = fields.Many2one('ned.packing', string='Packing', compute='compute_qc',store= True)

    mc = fields.Float(compute='compute_qc', store=True, string='Mc')
    fm = fields.Float(compute='compute_qc', store=True, string='Fm')
    black = fields.Float(compute='compute_qc', store=True, string='Black')
    broken = fields.Float(compute='compute_qc', store=True, string='Broken')
    brown = fields.Float(compute='compute_qc', store=True, string='Brown')
    mold = fields.Float(compute='compute_qc', store=True, string='Mold')
    cherry = fields.Float(compute='compute_qc', store=True, string='Cherry')
    excelsa = fields.Float(compute='compute_qc', store=True, string='Excelsa')
    screen18 = fields.Float(compute='compute_qc', string=">18%", store=True)
    screen16 = fields.Float(compute='compute_qc', string=">16%", store=True)
    screen13 = fields.Float(compute='compute_qc', string=">13%", store=True)
    screen12 = fields.Float(compute='compute_qc', string="<12%", store=True)
    greatersc12 = fields.Float(compute='compute_qc', string=">12%", store=True)
    burn = fields.Float(compute='compute_qc', string="Burn", store=True)
    eaten = fields.Float(compute='compute_qc', string="Eaten", store=True)
    immature = fields.Float(compute='compute_qc', string="Immature", store=True)
    stone_count = fields.Float(compute='compute_qc', string='Stone Count', store=True)
    stick_count = fields.Float(compute='compute_qc', string='Stick Count', store=True)

    
    #####
    
    

    @api.depends('analysis_upgrade_id.crop_id','analysis_upgrade_id')
    def _get_output_value(self):
        for this in self:
            if this.analysis_upgrade_id.crop_id:
                catalog_id = self.env['mrp.bom.premium'].search([('crop_id','=',this.analysis_upgrade_id.crop_id.id)], limit=1)
                if catalog_id:
                    exist_id = catalog_id.prem_ids.filtered(lambda x: x.product_id.id == this.product_id.id and this.product_id.categ_id.code not in('Lowgrades','Reject'))
                    if exist_id:
                        this.exportale = 'y'
                        this.required_mc = exist_id.mc
                        this.excess_mc = exist_id.mc - this.mc if exist_id.mc < this.mc else 0.0
                    else:
                        this.exportale = 'n'
                        this.required_mc = this.mc
    
    @api.model
    def get_low_grade(self):
        value_low_grade = 0.0
        for this in self:
            if this.exportale == 'y':
                value_low_grade = 0
            else:
                value_low_grade = 1 - (this.black * 0.3 + this.broken * 0.4 + this.brown * 0.2 + this.fm + this.mold * 0.5 + this.screen12 * 0.2 * (1 - (this.brown + this.black + this.broken + this.fm + this.mold) * 0.01) + this.cherry * 0.5) * 0.01
                if value_low_grade < 0:
                    value_low_grade = 0
        return value_low_grade

    
    @api.depends('exportale')
    def _get_value_low_grade(self):
        for this in self:
            if this.exportale == 'y':
                this.value_low_grade = 0
            else:
                value_low_grade = 1 - (this.black * 0.3 + this.broken * 0.4 + this.brown * 0.2 + this.fm + this.mold * 0.5 + this.screen12 * 0.2 * (1 - (this.brown + this.black + this.broken + this.fm + this.mold) * 0.01) + this.cherry * 0.5) * 0.01
                if value_low_grade < 0:
                    value_low_grade = 0
                this.value_low_grade = value_low_grade
                

    @api.depends('analysis_upgrade_id.price_premium','excess_mc','analysis_upgrade_id.liffe','analysis_upgrade_id.diff','analysis_upgrade_id.cost_price')
    def _get_mc_discount(self):
        for this in self:
            if this.analysis_upgrade_id.type == 'upgrade':
                this.mc_discount = (this.excess_mc*(this.analysis_upgrade_id.liffe + this.analysis_upgrade_id.diff - this.analysis_upgrade_id.cost_price))/100

    @api.depends('mc_discount','analysis_upgrade_id.liffe','analysis_upgrade_id.diff','analysis_upgrade_id.cost_price','value_low_grade')
    def _get_premium_discount(self):
        for this in self:
            if this.exportale == 'y':
                catalog_id = self.env['mrp.bom.premium'].search([('crop_id','=',this.analysis_upgrade_id.crop_id.id)], limit=1)
                exist_id = catalog_id.prem_ids.filtered(lambda x: x.product_id.id == this.product_id.id)
                this.premium_discount = exist_id.premium + this.mc_discount
            else:
                if this.product_id.default_code == 'GTR-70':
                    this.premium_discount = ((1 - this.fm/100 - 0.5*this.cherry/100)*0.6 -1)*(this.analysis_upgrade_id.liffe + this.analysis_upgrade_id.diff - this.analysis_upgrade_id.cost_price) + this.mc_discount
                else:
                    value_low_grade = this.value_low_grade
                    this.premium_discount = -(this.analysis_upgrade_id.liffe + this.analysis_upgrade_id.diff - this.analysis_upgrade_id.cost_price)*(1-value_low_grade) + this.mc_discount

    @api.depends('premium_discount','real_qty','analysis_upgrade_id.liffe','analysis_upgrade_id.diff','analysis_upgrade_id.cost_price')
    def _compute_value_input(self):
        for this in self:
            if this.product_id.default_code not in ('PCR','Dust','Husks','Stones','DSR'):
                if this.analysis_upgrade_id.type == 'upgrade':
                    this.value_input = abs(this.analysis_upgrade_id.liffe + this.analysis_upgrade_id.diff + this.premium_discount)*this.real_qty/1000

    analysis_upgrade_id = fields.Many2one('production.analysis',string="Report")

    exportale = fields.Selection([('n','N'),
                                    ('y','Y')],string='Exportable', compute='_get_output_value', store=True)
    value_low_grade = fields.Float(string="Value for Low Grade", compute='_get_value_low_grade', store=True)
    premium_discount = fields.Float(string='Premium/ Discount', compute='_get_premium_discount', store=True)
    required_mc = fields.Float(string='Required MC', compute='_get_output_value', store=True)
    excess_mc = fields.Float(string='Excess MC', compute='_get_output_value', store=True)
    mc_discount = fields.Float(string='MC Discount', compute='_get_mc_discount', store=True,digits=(12,2))
    value_input = fields.Float(string='Value Input  ', compute='_compute_value_input', store=True,digits=(12,2))

class ProductionAnalysisLineInputValue(models.Model):
    _name = "production.analysis.line.input.value"
    _order = 'id desc'


    @api.depends('contract_price','qty_allocation','liffe','exchange_rate')
    def _compute_raw_cost(self):
        for this in self:
            if this.contract_id.name[0:3] == 'NVP' and this.exchange_rate:
                this.raw_coffee_cost = this.contract_price/this.exchange_rate * this.qty_allocation
            else:
                this.raw_coffee_cost = this.qty_allocation*(this.liffe + this.contract_id.diff_price)/1000
            if this.exchange_rate:
                this.factory_price = (this.raw_coffee_cost+(-this.premium*this.qty_allocation + this.trucking_cost*this.qty_allocation)/this.exchange_rate)/this.qty_allocation*1000
    
    @api.depends('factory_price','qty_allocation')
    def _compute_paid(self):
        for this in self:
            this.total_paid = this.factory_price*this.qty_allocation/1000

    @api.depends('liffe','diff')
    def _compute_sale_ams(self):
        for this in self:
            this.sale_to_ams = this.liffe + this.diff

    @api.depends('sale_to_ams','analysis_id.cost_price')
    def _compute_price_factory_premium(self):
        for this in self:
            this.factory_price_premium = this.sale_to_ams - this.analysis_id.cost_price

    @api.depends('total_paid')
    def _compute_payment(self):
        for this in self:
            this.payment = this.total_paid

    @api.depends('factory_price','liffe','analysis_id.cost_price','diff','factory_price',)
    def _compute_premium(self):
        for this in self:
            if this.contract_id.type == 'consign' :
                this.premium_total = 0
            elif this.contract_id.type =='ptbf':
                this.premium_total = this.diff_price + this.analysis_id.cost_price - this.diff
            else:
                this.premium_total = this.factory_price - (this.liffe + this.diff - this.analysis_id.cost_price)
                
    @api.depends('diff_price','diff','analysis_id.cost_price','factory_price','trucking_cost','liffe','exchange_rate')
    def _compute_cross_check(self):
        for this in self:
            if this.contract_id.type == 'consign' :
                this.premium_total = 0
            elif this.contract_id.type =='ptbf':
                if this.exchange_rate:
                    this.premium_total = this.diff_price + this.analysis_id.cost_price - this.diff + this.trucking_cost/this.exchange_rate * 1000
            else:
                this.premium_total = this.factory_price -(this.liffe + this.diff - this.analysis_id.cost_price)
    
    analysis_id = fields.Many2one('production.analysis',string="Report")

    stack_id = fields.Many2one('stock.lot',string="Stack No.")
    picking_id = fields.Many2one('stock.picking',string="Picking")
    contract_id = fields.Many2one('purchase.contract',string='Contract No.')
    source_contract_id = fields.Many2one('purchase.contract', string='Source Contract')
    contract_price = fields.Float(string='Contract Price')
    qty_allocation = fields.Float(string='Payment Weight', digits=(12,0))
    premium = fields.Float(string='UTZ/4C (VND)', digits=(12,0))
    trucking_cost = fields.Float(string='Var -Trucking', digits=(12,0))
    raw_coffee_cost = fields.Float(string='Raw Coffee Cost (USD)', digits=(12,0),compute='_compute_raw_cost',store=True)
    factory_price = fields.Float(string='Factory Price (USD)', digits=(12,5),compute='_compute_raw_cost',store=True)
    total_paid = fields.Float(string='Total Paid (USD)', digits=(12,0),compute='_compute_paid',store=True)
    liffe = fields.Float(string='LIFFE (USD)', digits=(12,2))
    diff = fields.Float(string='DIFF (USD)', digits=(12,2))
    sale_to_ams = fields.Float(string='Sale to Ams (USD)', compute='_compute_sale_ams', store=True)
    factory_price_premium = fields.Float(string='Factory Price Premium (USD)', compute='_compute_price_factory_premium', store=True)
    payment = fields.Float(string="Payment", compute='_compute_payment', store=True)
    exchange_rate = fields.Float(string='Exchange Rate', digits=(12,0))
    premium_total = fields.Float(string='Cross check', compute='_compute_cross_check', store=True,digits=(12,2))
    diff_price = fields.Float(string='Diff to supplier', digits=(12,0))
    premium = fields.Float(string='UTZ/4C (VND)', digits=(12,0))
    subsidy = fields.Float(string='Subsidy', digits=(12,0))
#     cross_check = fields.Float(string='Cross check', compute='_compute_cross_check', store=True,digits=(12,2))
    
class ProductionAnalysisLineOutput(models.Model):
    _name = "production.analysis.line.output"
    _order = 'id desc'
    

    @api.depends('picking_id')
    def compute_qc(self):
        for this in self:
            if this.picking_id:
                for move in this.picking_id.move_line_ids_without_package.filtered(lambda r: r.product_id.id == this.product_id.id):
                    this.update({
                        'bag_no': move.bag_no,
                        'packing_id': move.packing_id,
                        'net_qty': move.init_qty,
                        'real_qty': move.init_qty if move.init_qty != 0 else move.product_uom_qty
                    })
                for kcs in this.picking_id.kcs_line.filtered(lambda r: r.product_id.id == this.product_id.id):
                    this.update({
                        'mc': kcs.mc,
                        'fm': kcs.fm,
                        'bb': kcs.black + kcs.broken,
                        'black': kcs.black,
                        'broken': kcs.broken,
                        'brown': kcs.brown,
                        'mold': kcs.mold,
                        'cherry': kcs.cherry,
                        'excelsa': kcs.excelsa,
                        'screen18': kcs.screen18,
                        'screen16': kcs.screen16,
                        'screen13': kcs.screen13,
                        'screen12': kcs.belowsc12,
                        'greatersc12': kcs.greatersc12,
                        'burn': kcs.burned,
                        'eaten': kcs.eaten,
                        'stone_count': kcs.stone_count,
                        'stick_count': kcs.stick_count,
                        'immature': kcs.immature,
                    })
                    
    @api.depends('analysis_id.crop_id','analysis_id')
    def _get_output_value(self):
        for this in self:
            if this.analysis_id.crop_id:
                catalog_id = self.env['mrp.bom.premium'].search([('crop_id','=',this.analysis_id.crop_id.id)], limit=1)
                if catalog_id:
                    exist_id = catalog_id.prem_ids.filtered(lambda x: x.product_id.id == this.product_id.id and this.product_id.categ_id.code not in('Lowgrades','Reject'))
                    if exist_id:
                        this.exportale = 'y'
                        this.required_mc = exist_id.mc
                        this.excess_mc = exist_id.mc - this.mc if exist_id.mc < this.mc else 0.0
                    else:
                        this.exportale = 'n'
                        this.required_mc = this.mc
                        this.excess_mc = 0
    
    @api.depends('exportale')
    def _get_value_low_grade(self):
        for this in self:
            if this.exportale == 'y':
                this.value_low_grade = 0
            else:
                value_low_grade = 1 - (this.black * 0.3 + this.broken * 0.4 + this.brown * 0.2 + this.fm + this.mold * 0.5 + this.screen12 * 0.2 * (1 - (this.brown + this.black + this.broken + this.fm + this.mold) * 0.01) + this.cherry * 0.5) * 0.01
                if value_low_grade < 0:
                    value_low_grade = 0
                this.value_low_grade = value_low_grade
    

    @api.depends('analysis_id.price_premium','excess_mc','analysis_id.liffe','analysis_id.diff','analysis_id.cost_price')
    def _get_mc_discount(self):
        for this in self:
            if this.analysis_id.type == 'upgrade':
                this.mc_discount = (this.excess_mc*(this.analysis_id.liffe + this.analysis_id.diff - this.analysis_id.cost_price))/100
            else:
                if this.analysis_id.price_premium:
                    this.mc_discount = (this.excess_mc*this.analysis_id.price_premium)/100

    @api.depends('mc_discount','analysis_id.sale_to_ams','analysis_id.cost_price')
    def _get_premium_discount(self):
        for this in self:
            if this.exportale == 'y':
                catalog_id = self.env['mrp.bom.premium'].search([('crop_id','=',this.analysis_id.crop_id.id)], limit=1)
                exist_id = catalog_id.prem_ids.filtered(lambda x: x.product_id.id == this.product_id.id)
                this.premium_discount = exist_id.premium + this.mc_discount
            else:
                if this.analysis_id.type == 'upgrade':
                    if this.product_id.default_code == 'GTR-70':
                        this.premium_discount = ((1 - this.fm/100 - 0.5*this.cherry/100)*0.6 -1)*(this.analysis_id.liffe + this.analysis_id.diff - this.analysis_id.cost_price)
                    else:
                        this.premium_discount = -(this.analysis_id.liffe + this.analysis_id.diff - this.analysis_id.cost_price)*(1-this.value_low_grade)
                else:
                    if this.product_id.default_code == 'GTR-70':
                        this.premium_discount = ((1 - this.fm/100 - 0.5*this.cherry/100)*0.6 -1)*(this.analysis_id.sale_to_ams - this.analysis_id.cost_price) + this.mc_discount
                    else:
                        this.premium_discount = -this.analysis_id.price_premium*(1-this.value_low_grade) + this.mc_discount

    @api.depends('premium_discount','real_qty','analysis_id.sale_to_ams','analysis_id.liffe','analysis_id.diff','analysis_id.cost_price')
    def _compute_value_output(self):
        for this in self:
            if this.product_id.default_code not in ('PCR','Dust','Husks','Stones','DSR','HUSKS','STONES'):
                if this.analysis_id.type == 'upgrade':
                    this.value_output = abs(this.analysis_id.liffe + this.analysis_id.diff + this.premium_discount)*this.real_qty/1000
                else:
                    this.value_output = abs(this.analysis_id.sale_to_ams+this.premium_discount)*this.real_qty/1000
            else:
                this.value_output = 0
                
    analysis_id = fields.Many2one('production.analysis',string="Report")
    
    stack_id = fields.Many2one('stock.lot',string="Stack No.")
    picking_id = fields.Many2one('stock.picking',string="Picking")
    date = fields.Date(string='Date')

    product_id = fields.Many2one('product.product',string="Product.", store=True)
    categ_id = fields.Many2one('product.category',string="Grade", store=True)
    
    zone_id = fields.Many2one('stock.zone',string='Zone', related='stack_id.zone_id', store=True)

    net_qty = fields.Float(compute='compute_qc', store=True, string ="Net Weight", digits=(12,0))
    real_qty = fields.Float(compute='compute_qc', store=True, string ="Real Weight", digits=(12,0))

    bag_no = fields.Float(string='Bag No', compute='compute_qc', store=True, digits=(12,0))
    packing_id = fields.Many2one('ned.packing', string='Packing',compute='compute_qc', store = True)

    mc = fields.Float(compute='compute_qc', store=True, string='Mc')
    fm = fields.Float(compute='compute_qc', store=True, string='Fm')
    bb = fields.Float(compute='compute_qc', store=True, string='Black & Broken')
    black = fields.Float(compute='compute_qc', store=True, string='Black')
    broken = fields.Float(compute='compute_qc', store=True, string='Broken')
    brown = fields.Float(compute='compute_qc', store=True, string='Brown')
    mold = fields.Float(compute='compute_qc', store=True, string='Mold')
    cherry = fields.Float(compute='compute_qc' ,store=True, string='Cherry')
    excelsa = fields.Float(compute='compute_qc' ,store=True, string='Excelsa')
    screen18 = fields.Float(compute='compute_qc', string =">18%", store=True)
    screen16 = fields.Float(compute='compute_qc', string =">16%", store=True)
    screen13 = fields.Float(compute='compute_qc', string =">13%", store=True)
    screen12 = fields.Float(compute='compute_qc', string ="<12%", store=True)
    greatersc12 = fields.Float(compute='compute_qc', string =">12%", store=True)
    burn = fields.Float(compute='compute_qc', string ="Burn", store=True)
    eaten = fields.Float(compute='compute_qc', string ="Eaten", store=True)
    immature = fields.Float(compute='compute_qc', string ="Immature", store=True)
    stone_count = fields.Float(compute='compute_qc', string='Stone Count', store= True)
    stick_count = fields.Float(compute='compute_qc', string='Stick Count', store= True)
    state = fields.Selection(related='picking_id.state', string='State')

    exportale = fields.Selection([('n','N'),
                                    ('y','Y')],string='Exportable', compute='_get_output_value', store=True)
    value_low_grade = fields.Float(string="Value for Low Grade", compute='_get_value_low_grade', store=True)
    premium_discount = fields.Float(string='Premium/ Discount', compute='_get_premium_discount', store=True)
    required_mc = fields.Float(string='Required MC', compute='_get_output_value', store=True)
    excess_mc = fields.Float(string='Excess MC', compute='_get_output_value', store=True)
    mc_discount = fields.Float(string='MC Discount', compute='_get_mc_discount', store=True,digits=(12,2))
    value_output = fields.Float(string='Value Output', compute='_compute_value_output', store=True,digits=(12,2))



class ProductionAnalysisLineDailyConfirmation(models.Model):
    _name = "production.analysis.line.daily.confirmation"
    _order = 'id desc'

    analysis_id = fields.Many2one('production.analysis',string="Report")

    contract_id = fields.Many2one('purchase.contract', string='Contract No.')
    liffe = fields.Float(string='LIFFE')
    diff = fields.Float(string='DIFF')
    diff_price = fields.Float(string='Diff to supplier')
    exchange_rate = fields.Float(string='Exchange Rate')
    

class MrpProduction(models.Model):
    _inherit = 'mrp.production'
    
    report_pnl = fields.Boolean('Batch Report')
    
    
    def action_done(self):
        res = super(MrpProduction, self).action_done()
        for this in self:
            type ='normal'
            if this.name[0:3] != 'BTA':
                type = 'upgrade'
            analysis_ids = self.env['production.analysis'].search([('production_id','=',this.id)])
            if analysis_ids:
                if analysis_ids.type =='normal':
                    analysis_ids.load_data()
                else:
                    analysis_ids.load_data_upgrade()
            else:
                analysis = self.env['production.analysis'].create({'production_id':this.id,'type':type})
                if type =='normal':
                    analysis.load_data()
                else:
                    analysis.load_data_upgrade()
                # if this.company_id.res_user_ids:
                #     self.send_mail(analysis)
        return res
    
    def send_mail(self,report):
        for this in self:
            MailMessage = self.env['mail.message']
            emails = self.env['mail.mail']
            base_template = self.env.ref('mail.mail_template_data_notification_email_default')
            #body: Description
            body = 'Description: ' + this.name
                
            values = {
                'model': 'production.analysis',
                'res_id': report.id,
                'body': body,
                'subject': 'Batch Report',
                'partner_ids': [(4, [x.partner_id.id for x in this.company_id.res_user_ids])]
            }
            # Avoid warnings about non-existing fields
            for x in ('from', 'to', 'cc'):
                values.pop(x, None)
            try:
                # Post the message
                new_message = MailMessage.create(values)
                partner = self.env['res.partner']
                base_template_ctx = partner._notify_prepare_template_context(new_message)
                base_mail_values = partner._notify_prepare_email_values(new_message)
                
                recipients = self._message_notification_recipients(new_message, partner)
                for email_type, recipient_template_values in recipients.iteritems():
                    # generate notification email content
                    template_fol_values = dict(base_template_ctx, **recipient_template_values)  # fixme: set button_unfollow to none
                    template_fol_values['button_follow'] = False
                    template_fol = base_template.with_context(**template_fol_values)
                    # generate templates for followers and not followers
                    fol_values = template_fol.generate_email(new_message.id, fields=['body_html', 'subject'])
                    # send email
                    new_emails, new_recipients_nbr = partner._notify_send(fol_values['body'], fol_values['subject'], recipient_template_values['followers'], **base_mail_values)
                    emails |= new_emails
                emails.send()
            except:
                pass
    
    
    
    
    

