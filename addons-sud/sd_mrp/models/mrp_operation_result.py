# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _, tools
import time
from datetime import timedelta
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"    
from odoo.exceptions import UserError, ValidationError

from datetime import datetime


class MrpOperationResult(models.Model):
    _name = 'mrp.operation.result'
    _description = 'Operation Result'
    _inherit = ['mail.thread']
    # _order = 'start_date'
    
    def button_load(self):
        return
    
    def unlink(self):
        if not self.env.user.user_has_groups('sd_mrp.group_delete_mrp_production_result'):
            raise UserError(_('You cannot delete records of this model!'))
        res = super(MrpOperationResult, self).unlink()
        
    
    def check_state(self):
        line = self.produced_products.filtered(lambda r: r.picking_id.id == False)
        if line:
            return False
        else:
            return True
        
    def btt_confirm(self):
        for i in self.produced_products.filtered(lambda r: r.picking_id.id == False):
            i.create_kcs()
        if self.check_state():
            self.state = 'done'
        
    
    def _get_hours(self):
        res = {}
        for line in self.browse(cr, uid, ids):
            res[line.id] = 0.0
            start_date = datetime.strptime(line.start_date, DEFAULT_SERVER_DATETIME_FORMAT)
            end_date = datetime.strptime(line.end_date, DEFAULT_SERVER_DATETIME_FORMAT)
            if end_date > start_date:
                diff_hours = round(float((end_date - start_date).seconds) / 3600, 2)
                res[line.id] = diff_hours
        return res
    
    def _sum_qty(self):
        res = {}
        for line in self.browse(cr, uid, ids):
            res[line.id] = 0.0
            for result in line.produced_products:
                res[line.id] += result.product_qty
        return res
    
    # def _get_result(self):
    #     result = {}
    #     for line in self.'mrp.operation.result.produced.product').browse(cr, uid, ids, context=context):
    #         result[line.operation_result_id.id] = True
    #     return result.keys()
    
    def _default_warehouse(self):
        warehouse_ids = self.env['stock.warehouse'].with_context(user_workers=True).search(
            [('company_id', '=', self.env.user.company_id.id)])
        # default with user only working 1 company account analytic
        if warehouse_ids:
            return warehouse_ids[0]
    
    @api.model
    def _domain_warehouse(self):
        return "[('id', 'in', %s)]" % self.env.user._warehouses_domain()
    
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=False, default=_default_warehouse, domain=lambda self: self._domain_warehouse())
    name= fields.Char('Reference', required=False, states={'done': [('readonly', True)], 'cancel' :[('readonly', True)]})
    operation_id = fields.Many2one('mrp.workorder', 'Workorder Order', required=False, 
                                    states={'done':[('readonly', True)], 'cancel':[('readonly', True)]}, ondelete='cascade')
    production_id = fields.Many2one('mrp.production', string="Manufacturing Order", readonly=False)
    #Thấy không cần
    # finished_good_id= fields.Many2one(related= 'operation_id.production_id.product_id',  string="Finished good", readonly=True)
    calendar_id= fields.Many2one('resource.calendar', 'Shift', required=False, states={'done': [('readonly', True)], 'cancel':[('readonly', True)]})
    start_date= fields.Datetime('Start date', required=True, states={'done':[('readonly', True)], 'cancel':[('readonly', True)]}, default= time.strftime(DATE_FORMAT))
    end_date= fields.Datetime('End date', required=True, states={'done':[('readonly', True)], 'cancel':[('readonly', True)]}, default= time.strftime(DATE_FORMAT))
    congdoan_id= fields.Many2one('mrp.production.stage', 'Production stage')
    hours= fields.Float(string="Hours", readonly=True)
    product_id= fields.Many2one('product.product', string='Product', required=False, readonly=True, states={'draft': [('readonly', False)]})
    product_qty= fields.Float(compute = '_sum_qty',  string='Product Quantity', store = True)
    #
    product_uom= fields.Many2one('uom.uom', string= 'UoM',required=False, readonly=True, states={'draft': [('readonly', False)]})
    resource_id= fields.Many2one('mrp.workcenter', 'Resource', required=False, readonly=False, states={'draft' :[('readonly', False)]})
    
    produced_products= fields.One2many('mrp.operation.result.produced.product', 'operation_result_id', string= 'Produced Products', readonly=True, states={'draft': [('readonly', False)]})
    consumed_products= fields.One2many('mrp.operation.result.consumed.product', 'operation_result_id', string= 'Consumed Products', readonly=True, states={'draft': [('readonly', False)]})
    #
    date_result = fields.Date(string="Date result", default= datetime.now())
    note= fields.Text('Notes')
    write_date=  fields.Datetime('Last Modification', readonly=True)
    create_date= fields.Datetime('Creation Date', readonly=True)
    write_uid=  fields.Many2one('res.users', 'Updated by', readonly=True)
    create_uid= fields.Many2one('res.users', 'Created by', readonly=True)
    state= fields.Selection([
        ('draft', 'Draft'),
        ('cancel', 'Cancelled'),
        ('done', 'Done'),
        ('transfered','Stock Transfered')
        ], 'Status', readonly=True, default='draft')
    
    finished = fields.Boolean('Finished',readonly=True, states={'draft': [('readonly', False)]})
    
    direct_labour = fields.One2many('direct.labour', 'result_id', 'Direct Labour', readonly=True, states={'draft': [('readonly', False)]})
    production_shift =fields.Selection([
                        ('1','Ca 1'),
                        ('2','Ca 2'),
                        ('3','Ca 3'),], 'Ca', required=True, default="1" )
    
    
    import_result_id = fields.Many2one('wizard.import.production.result', string="import")
    
    @api.depends('produced_products')
    def _total_qty(self):
        for i in self:
            total_qty = 0
            total_bag = 0
            for line in i.produced_products:
                total_qty += line.product_qty
                total_bag += line.qty_bags
            i.total_qty = total_qty
            i.total_bag = total_bag
            
    total_qty = fields.Float(compute='_total_qty',digits=(16,2) , string = 'Total Qty',store=True)
    total_bag = fields.Float(compute='_total_qty',digits=(16,2) , string = 'Total Bag',store=True)
    user_import_id = fields.Many2one('res.users', string='User',copy=False)
    resource_calendar_id = fields.Integer(string ='Working Time')
    
    # def _get_default_calendar_id(self):
    #     calendar_ids = self.pool.get('resource.calendar').search(cr, uid, [], context=context)
    #     return calendar_ids and calendar_ids[0] or False
    #
    # @api.model
    # def default_get(self, default_fields):
    #     res = super(MrpOperationResult, self).default_get(default_fields)
    #     if 'operation_id' in res:
    #         operation_id = res['operation_id']
    #         operation_obj = self.env['mrp.production.workcenter.line'].browse(operation_id)
    #         res.update({'product_id': operation_obj.product_id.id,'product_uom': operation_obj.product_uom.id})
    #     return res
    
    _defaults = {
        # 'calendar_id':_get_default_calendar_id,
        'state': 'draft',
        'start_date': time.strftime('%Y-%m-%d %H:%M:%S'),
        'name': 'New'
    }
    
    # def copy(self):
    #     if default is None:
    #         default = {}
    #     default.update({
    #         'name':'New',
    #         'state': 'draft',
    #         'start_date': time.strftime('%Y-%m-%d %H:%M:%S'), 
    #     })
    #     return super(MrpOperationResult, self).copy()
    #
    # def onchange_operation(self):
    #     res = domain = {}
    #     if operation_id:
    #         operation_obj = self.pool.get('mrp.production.workcenter.line').browse(cr, uid, operation_id)
    #         res = {'product_id': operation_obj.product_id.id or False,  'product_uom': operation_obj.product_uom.id or False,
    #           'resource_id': operation_obj.workcenter_id.id or False, 'congdoan_id': operation_obj.congdoan_id.id or False}
    #         domain = {'product_id': [('id','=',operation_obj.product_id.id)],
    #                   'product_uom': [('id','=',operation_obj.product_uom.id)]}
    #     return {'value': res, 'domain': domain} 
    
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('mrp.operation.result')
        return super(MrpOperationResult, self).create(vals)
