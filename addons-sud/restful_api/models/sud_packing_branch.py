# -*- coding: utf-8 -*-
import time
from datetime import timedelta
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"    
from datetime import datetime
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

class NedPacking(models.Model):
    _inherit = 'ned.packing'
    
    packing_ids = fields.One2many('sud.packing.branch','packing_id',string="Packing")

class SudPackingBranch(models.Model):
    _name = 'sud.packing.branch'
    _description = "Pallets Branch"
    _order = 'id desc'
    _inherit = ['mail.thread']

    def _default_warehouse(self):
        warehouse_ids = self.env['stock.warehouse'].with_context(user_workers=True).search(
            [('company_id', '=', self.env.user.company_id.id)])
        # default with user only working 1 company account analytic
        if warehouse_ids:
            return warehouse_ids[0]
    @api.model
    def _domain_warehouse(self):
        return "[('id', 'in', %s)]" % self.env.user._warehouses_domain()

    @api.depends('repair_line')
    def _tare_weight(self):
        new_weight = tare_weight = 0.0
        for this in self:
            for line in this.repair_line:
                if line.state in ('cancel'):
                    continue
                tare_weight = line.tare_weight_new
            this.update({'tare_weight': tare_weight})

    name = fields.Char(string="Spare-Code")
    description_name = fields.Char(string="Description Name",size=256,required=True)
    packing_id = fields.Many2one('ned.packing', string='Type', required=True)
    dimension = fields.Char(string="Dimension (LxWxH)",size=256)
    # tare_weight = fields.Float(string="Tare weight",digits=(16,2))
    tare_weight = fields.Float(compute='_tare_weight',string="Tare weight",digits=(16,2), store=True)
    warehouse_id = fields.Many2one('stock.warehouse',string="Warehouse", default=_default_warehouse, domain=lambda self: self._domain_warehouse())
    repair_line = fields.One2many('sud.packing.branch.line', 'repair_id', string='Repair History', 
                       readonly=True, states={'draft': [('readonly', False)]}, copy=True)
    state = fields.Selection([('draft', 'New'),('done', 'Done'),('cancel','Canceled')], string='Status',
                             readonly=True, copy=False, index=True, default='draft')
    scale_id = fields.Integer('Scale ID', readonly=True)
    user_import_id = fields.Many2one('res.users', string='User',copy=False)
    packing_branch_ids = fields.One2many('mrp.operation.result.scale','packing_branch_id',string="Packing Branch")


    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('sud.packing.branch')
        result = super(SudPackingBranch, self).create(vals)
        return result

    def button_done(self):
        for this in self:
            if this.state =='draft':
                this.state ='done'
                
    def unlink(self):
        for record in self:
            if record.state not in ('draft', 'cancel'):
                raise UserError(_('You cannot delete is not draft or cancelled.'))
        return super(SudPackingBranch, self).unlink()

    def button_draft(self):
        for request in self:
            request.state = 'draft'

    # @api.onchange('repair_line')
    # def _tare_weight_line_change(self):
    #     new_weight = 0.0

    #     for this in self:
    #         for line in this.repair_line:
    #             if line.state in ('cancel'):
    #                 continue
    #             new_weight = line.tare_weight_new
    #             print(new_weight)
    #         this.tare_weight = new_weight


class SudPackingBranchLine(models.Model):
    _name = "sud.packing.branch.line"
    _description = "Repair History Line"
    

    # @api.depends('tare_weight_new')
    # def _compute_old_tare(self):
    #     current_tare = 0.0
    #     for this in self:
    #         if this.state in ('cancel'):
    #             continue
    #         this.update({'tare_weight_old': current_tare})
    #         current_tare = this.tare_weight_new

    @api.onchange('tare_weight_new')
    def _tare_weight_change(self):
        current_weight = 0.0
        for line in self:
            if line.state in ('cancel'):
                continue
            line.tare_weight_old = current_weight
            current_weight = line.tare_weight_new

 
    repair_id = fields.Many2one('sud.packing.branch', string='Repair History')
    repair_reason = fields.Char(string="Repair reason",size=256,required=True)
    # tare_weight_old = fields.Float(compute='_compute_old_tare', string="Old Tare weight", digits=(16,2), store=True)
    tare_weight_old = fields.Float(string="Old Tare weight",digits=(16,2))
    tare_weight_new = fields.Float(string="New Tare weight",digits=(16,2))
    state = fields.Selection([('done', 'Done'),('cancel','Canceled')], string='Status',
                             readonly=True, copy=False, index=True, default='done')
    scale_id = fields.Integer('Scale ID', readonly=True)
    scale_line_id = fields.Integer('Scale Line ID', readonly=True)
    user_import_id = fields.Many2one('res.users', string='User',copy=False, default=lambda self: self._uid)




