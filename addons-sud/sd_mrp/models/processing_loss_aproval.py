# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from datetime import datetime

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime, timedelta

class ProcessingLossAproval(models.Model):
    _name = "processing.loss.aproval"
    
    # emp_id = fields.Many2one('hr.employee', 'Employee', required=True)
    # job_id = fields.Many2one('hr.job', 'Job')
    # department_id = fields.Many2one('hr.department', 'Department')
    # hour_nbr =  fields.Float('Number of Hours', required=True)
    # result_id = fields.Many2one('mrp.operation.result', 'Operation Result')
    # ot_hour = fields.Float('Number of OT Hours')
    
    production_id = fields.Many2one('mrp.production',string="Batch No",required =True)
    batch_type = fields.Char(related='production_id.bom_id.type_code',string ='Batch type',readonly =True,store =True)
    product_issued = fields.Float(related='production_id.product_issued', string ="Weight In",readonly =True,store =True, digits=(16,2))
    product_received = fields.Float(related='production_id.product_received', string ="Weight Out",readonly =True,store =True, digits=(16,2))
    mc_in = fields.Float(compute='compute_qc', store=True, string='MC In', digits=(16,2))
    mc_out = fields.Float(compute='compute_qc', store=True, string='MC Out', digits=(16,2))
    weight_loss = fields.Float(string='Weight Loss', digits=(16,2))
    physical_weight = fields.Float(compute='compute_qc', store=True, string='Physical loss (kg)', digits=(16,2))
    mc_loss = fields.Float(compute='compute_qc', store=True, string='MC Loss', digits=(16,2))
    physical_loss = fields.Float(compute='compute_qc', store=True, string='Physical Loss', digits=(16,2))
    invisible_loss = fields.Float(compute='compute_qc', store=True, string='Invisible Loss', digits=(16,2))
    state = fields.Selection([("draft", "Draft"),("approved", "Approved")], string="Status", 
                             readonly=True, copy=False, index=True, default='draft')
    picking_id = fields.Many2one('stock.picking',string="GRP LOSS",required =True)
    start_date = fields.Datetime(related='production_id.date_planned_start',string='Start Date',readonly =True,store =True)
    end_date = fields.Datetime(related='picking_id.date_done',string='End Date',readonly =True,store =True) 
    warehouse_id = fields.Many2one('stock.warehouse', related='production_id.warehouse_id', store=True)
    
    
    @api.depends('production_id','product_issued','product_received','picking_id.state','state')
    def compute_qc(self):
        for this in self:
            if this.production_id:
                sql = '''
                SELECT SUM(rkl.mc * rkl.product_qty)/SUM(rkl.product_qty) mc 
                FROM mrp_production mp
                    JOIN stock_move_line stm ON mp.id = stm.material_id
                    JOIN stock_picking sp ON sp.id = stm.picking_id
                    join stock_picking_type spt on sp.picking_type_id = spt.id
                    JOIN request_kcs_line rkl ON rkl.picking_id = sp.id
                WHERE mp.id =%s 
                AND sp.state= 'done'
                AND spt.code ='production_out';
                '''%(this.production_id.id)
                self._cr.execute(sql)
                for line in self._cr.dictfetchall():
                    this.mc_in = line['mc'] or 0.0
                    
                sql = '''
                SELECT SUM(rkl.mc * rkl.product_qty)/SUM(rkl.product_qty) mc 
                FROM mrp_production mp
                    JOIN stock_move_line stm ON mp.id = stm.finished_id
                    JOIN stock_picking sp ON sp.id = stm.picking_id
                    join stock_picking_type spt on sp.picking_type_id = spt.id
                    JOIN request_kcs_line rkl ON rkl.picking_id = sp.id
                WHERE mp.id =%s 
                AND spt.code ='production_in'    
                AND stm.state= 'done';
                '''%(this.production_id.id)
                self._cr.execute(sql)
                for line in self._cr.dictfetchall():
                    this.mc_out = line['mc'] or 0.0  
                    
                this.mc_loss = this.mc_in - this.mc_out
                this.physical_weight = this.product_issued - this.product_received
                this.physical_loss = this.product_issued and (this.physical_weight/this.product_issued * 100) or 0
                this.invisible_loss = this.physical_loss - this.mc_loss  
    
    def button_reopen(self):
        for this in self:
            if this.picking_id.state == 'done':
                this.picking_id.btt_reopen_stock()
            this.picking_id.state ='assigned'
            this.state = 'draft'
    
    def button_compute(self):
        for i in self:
            i.compute_qc()
    
    def button_approve(self):
        for this in self:
            this.compute_qc()
            this.picking_id.date_done = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            this.picking_id.button_sd_validate()
            this.picking_id.state_kcs = 'approved'
        this.state = 'approved'
        return
                
    