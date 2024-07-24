# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from odoo.tools import float_round
import time
DATE_FORMAT = "%Y-%m-%d"


class StockStack(models.Model):
    _name = "stock.stack"
    _order = 'create_date desc, id desc'
    _inherit = ['mail.thread']
    
    name = fields.Char(string='Code', required=False, size=128, default='/')
    
    
    # def name_get(self):
    #     result = []
    #     for rc in self:
    #         name = rc.name
    #         if rc.code:
    #             if self.env['res.users'].browse(self.env.context.get('uid', 1)).has_group('__export__.res_groups_240'):
    #                 name = rc.code
    #         result.append((rc.id, name))
    #     return result
    #
    # def unlink(self):
    #     for record in self:
    #         for line in record.qc_line_ids:
    #             line.unlink()
    #         if record.move_ids:
    #             raise UserError(_('You can not delete Stack'))
    #     return super(StockStack, self).unlink()
    #
    # @api.constrains('name')
    # def _check_name_duplicate(self):
    #     #Kiet: check duplicate Code (Stack)
    #     if self.name:
    #         e_ids = self.search([('id','!=',self.id),('name','=',self.name)])
    #         if len(e_ids):
    #             raise UserError(("name '%s' is already exist for Stack '%s'!")%(self.name, self.name)) 
    #
    # def stack_reports(self):
    #     return {
    #             'type': 'ir.actions.report.xml',
    #             'report_name':'report_stack',
    #             }
    #
    # @api.model_create_multi
    # def create(self, vals_list):
    #     for vals in vals_list:
    #         if 'company_id' in vals:
    #             self = self.with_company(vals['company_id'])
    #         if vals.get('name', _("New")) == _("New"):
    #             seq_date = fields.Datetime.context_timestamp(
    #                 self, fields.Datetime.to_datetime(vals['date_order'])
    #             ) if 'date_order' in vals else None
    #             vals['name'] = self.env['ir.sequence'].next_by_code(
    #                 'sale.order', sequence_date=seq_date) or _("New")
    #
    #     return super().create(vals_list)
    #
    #
    # @api.model_create_multi
    # def create(self, vals_list):
    #     for vals in vals_list:
    #         if 'name' not in vals:
    #             if 'hopper' in vals and vals['hopper']:
    #                 vals['name'] = self.env['ir.sequence'].next_by_code('stock.stack.hopper.seq') or 'New'
    #             else:
    #                 vals['name'] = self.env['ir.sequence'].next_by_code('stock.sack.seq') or 'New'
    #
    #         if 'name' in vals and not vals['name']:
    #             if 'hopper' in vals and vals['hopper']:
    #                 vals['name'] = self.env['ir.sequence'].next_by_code('stock.stack.hopper.seq') or 'New'
    #             else:
    #                 vals['name'] = self.env['ir.sequence'].next_by_code('stock.sack.seq') or 'New'
    #
    #         if 'date' not in vals:
    #             vals['date'] =  time.strftime(DATE_FORMAT)
    #
    #     for i in super().create(vals_list):
    #         if 'p_contract_id' in vals and vals['p_contract_id'] :
    #             self.env['s.contract'].browse(vals['p_contract_id']).write({'wr_line': i.id})
    #
    #     return result
    #
    # @api.model
    # @api.depends('move_ids','move_ids.state','move_ids.product_uom_qty','move_ids.location_id','move_ids.location_dest_id','stack_empty', 'is_bonded', 'out_qty')
    # def _get_remaining_qty(self):
    #     uom_obj = self.env['uom.uom']
    #     for stack in self:
    #         stack_qty = remaining_qty = 0.0
    #         rounding = 0.0
    #         init =0.0
    #         bag_qty = 0
    #         for move_line in stack.move_ids:
    #             # qty = uom_obj._compute_qty_obj(move_line.product_uom, move_line.product_uom_qty,
    #             #                    move_line.product_id.uom_id, product_id=move_line.product_id.id)
    #             qty = move_line.product_uom_qty
    #             # init_qty = uom_obj._compute_qty_obj(move_line.product_uom, move_line.init_qty,
    #             #                    move_line.product_id.uom_id, product_id=move_line.product_id.id)
    #             init_qty = move_line.init_qty
    #             rounding = move_line.product_id.uom_id.rounding
    #             #Kiet: nhap kho
    #             if move_line.location_dest_id.usage in ('internal','procurement') and move_line.location_id.usage not in ('internal','procurement') and move_line.state == 'done':
    #                 remaining_qty += qty 
    #                 stack_qty += qty
    #                 init += init_qty
    #                 bag_qty += move_line.bag_no
    #
    #             if move_line.location_dest_id.usage not in ('internal') and move_line.location_id.usage in ('internal') and move_line.state == 'done':
    #                 #kiet: Trừ dòng xuất tiêu thụ ra vì đã trừ rồi
    #                 if move_line.location_dest_id.usage in ('production') and move_line.location_id.usage in ('internal') and move_line.state == 'done':
    #                     continue
    #                 remaining_qty -= qty 
    #                 init -= init_qty
    #                 bag_qty -= move_line.bag_no or 0.0
    #
    #             if move_line.location_dest_id.usage in ('internal') and move_line.location_id.usage in ('internal') and move_line.state == 'done':
    #                 remaining_qty -= qty 
    #                 init -= init_qty
    #                 bag_qty -= move_line.bag_no or 0.0
    #
    #         if stack.is_bonded and stack.qc_line_ids:
    #             stack.init_qty = stack.qc_line_ids[0].instored
    #             stack.remaining_qty = stack.qc_line_ids[0].instored - stack.out_qty
    #         else:
    #             if stack.stack_empty:
    #                 stack.init_qty = 0
    #             else:
    #                 stack.init_qty = init
    #             stack.remaining_qty = remaining_qty
    #
    #         stack.stack_qty = stack_qty
    #         stack.bag_qty = bag_qty
    
    
    # bag_qty = fields.Float(  string='Bag',store=True, digits=(12, 0),)
    # stack_qty = fields.Float( string='Basis Weight',store=True, digits=(12, 0),)
    # init_qty = fields.Float(string='Net Weight',store=True, digits=(12, 0),)
    # out_qty = fields.Float( string='Ex Weight', digits=(12, 0))
    # remaining_qty = fields.Float(  string='Remain Weight', digits=(12, 0),)
    # name = fields.Char(string='Code', required=False, size=128, default='/')
    # code = fields.Char(string='WR No', required=False, size=128)
    # date = fields.Date(string="Date")
    # zone_id = fields.Many2one('stock.zone', string='Zone',  ondelete='cascade',  copy=False)
    # active = fields.Boolean(string='Active',default = True,)
    # move_ids = fields.One2many('stock.move', 'stack_id' ,'Move Line',)
    # province_id = fields.Many2one('res.country.state','Province',)
    # delivery_place_id = fields.Many2one('delivery.place','Delivery Place')
    # lock = fields.Boolean(string='Lock',default = False,)
    # p_contract_id = fields.Many2one('s.contract', string='P Contract')
    # allocation_ids = fields.Many2many('sale.contract', compute='get_allocation_ids', string='Allocation')
    # allocated_qty = fields.Float(string='Allocated Qty', compute='get_allocation_ids')
    # allocated_bag = fields.Float(string='Allocated Bag', compute='get_allocation_ids')
    # unallocated_qty = fields.Float(string='Unallocated Qty', compute='get_allocation_ids')
    # unallocated_bag = fields.Float(string='Unallocated Bag', compute='get_allocation_ids')
    # shipment_id = fields.Many2many('shipping.instruction', 'stack_shipment_rel', 'stack_id', 'shipment_id', string='Shipments')
    #
    # doc_weight = fields.Float(string='Docs Weight', digits=(12, 2))
    #
    # # ned KCS VN
    # allocate_qty = fields.Float(string='Allocated Qty', compute='_compute_allocated_qty')
    # stack_on_hand = fields.Char(string='Real Stack Export')
    #
    #
    # def _compute_allocated_qty(self):
    #     for i in self:
    #         sale_contract_detail_draft = self.env['sale.contract.deatail'].search([
    #             ('stack_id', '=', i.id),
    #             ('sp_id', '!=', False)
    #         ])
    #         if sale_contract_detail_draft:
    #             i.allocate_qty = sum(detail.tobe_qty for detail in sale_contract_detail_draft)
    #         else:
    #             i.allocate_qty = 0
    #
    # #Kiet du
    # # stack_his_ids = fields.Many2many('stock.stack.transfer', 'transfer_stack_rel', 'stack_id', 'transfer_id', string='Stack', readonly=True,)
    # product_id = fields.Many2one(related='move_ids.product_id',  string='Product',store=True)
    # categ_id = fields.Many2one(related='move_ids.product_id.categ_id',  string='Category',store=True)
    # bank_id = fields.Many2one('res.bank', string='Banks', readonly=True)
    # mortgage_amount = fields.Monetary(string='Amount',readonly=True, )
    # currency_id = fields.Many2one('res.currency', string='Currency')
    # limit_qty = fields.Float(string='Limit Qty',digits=(12, 0))
    #
    # production_id = fields.Many2one('mrp.production', string='Manufacturing Orders')
    #
    # contract_id = fields.Many2one('s.contract', string='SNo.')
    #
    # #Kiet ko sai
    # # expenses_ids = fields.One2many('expenses.stack', 'stack_id' ,'Expenses')
    #
    # #Kiet ko sai
    # #loss_ids = fields.One2many('loss.stack', 'stack_id' ,'Los',)
    #
    # #Kiet ko sai 
    # #allocation_npe_ids = fields.One2many('stack.nvp.relation', 'stack_id' ,'Allocation NPE',)
    # districts_id = fields.Many2one('res.district', string='Source', ondelete='restrict')
    # picking_id = fields.Many2one(related ='move_ids.picking_id',  string='Picking',store=True)
    # pledged = fields.Char(string="Pledged.")
    # warehouse_id = fields.Many2one(related='zone_id.warehouse_id',  string='Warehouse',store = True)
    # stack_type = fields.Selection([
    #     ('pallet', 'Pallet'),
    #     ('stacked', 'Stacked'),
    #     ('pile', 'Pile'),
    #     ('jum_1', 'Jum-1.0'),
    #     ('jum_1_3', 'Jum-1.3'),
    #     ('jum_1_5', 'Jum-1.5'),
    #     ('stack_wip', 'Stack Wip'),
    #     ('hp', 'Hopper')
    # ],
    # string='Stack type', default='stacked')
    # is_bonded = fields.Boolean(string='Is Bonded')
    # stack_empty = fields.Boolean('Stack empty', default = False)
    # shipper_id = fields.Many2one('res.partner', string='Shipper')
    #
    # def change_product(self):
    #     if self.move_ids:
    #         for move in self.move_ids:
    #             move.action_cancel()
    #             move.product_id = self.product_change_id.id
    #             move.picking_id.product_id = self.product_change_id.id
    #             move.action_done()
    #     #Change product for QC Picking
    #         sql = '''
    #             UPDATE request_kcs_line set product_id = %s
    #             WHERE stack_id = %s
    #         '''%(self.product_change_id.id,self.id)
    #         self.env.cr.execute(sql)
    #         # print sql
    #         # print self.env.cr.execute(sql)
    #
    # product_change_id = fields.Many2one('product.product', string='Change Product')
    #
    # # @api.depends('allocation_npe_ids','allocation_npe_ids.product_qty',)
    # # def _total_qty(self):
    # #     for order in self:
    # #         total_allocation = 0
    # #         for line in order.allocation_npe_ids:
    # #             total_allocation +=line.product_qty
    # #         order.total_allocation = total_allocation
    # #         order.total_remain = order.remaining_qty - total_allocation
    # #
    # # total_allocation = fields.Float(compute='_total_qty',digits=(16,0) , string = 'Allocation Qty',store=True)
    # # total_remain = fields.Float(compute='_total_qty',digits=(16,0) , string = 'Remain Qty',store=True)
    #
    # def get_default_zone(self, warehouse_id):
    #     zone_obj = self.env['stock.zone']
    #     warehouse_obj = self.env['stock.warehouse']
    #     wh_info = warehouse_obj.browse(warehouse_id)
    #     zone_id = zone_obj.search([('warehouse_id', '=', warehouse_id)], limit=1)
    #     if not zone_id:
    #         zone_id = zone_obj.create({
    #             'name': '%s Zone' % wh_info.code,
    #             'warehouse_id': warehouse_id,
    #             'description': '%s Zone' % wh_info.code,
    #             'active': True
    #         })
    #     zone_id = zone_id and zone_id.id or 0
    #     return zone_id
    #
    # @api.onchange('p_contract_id')
    # def p_contract_change(self):
    #     if self.p_contract_id:
    #         self.name = 'WR-%s' % (self.p_contract_id.name or '')
    #         self.product_id = self.p_contract_id.standard_id and self.p_contract_id.standard_id.id or 0
    #         warehouse_id = self.p_contract_id.warehouse_id and self.p_contract_id.warehouse_id.id or 0
    #         if warehouse_id:
    #             self.zone_id = self.get_default_zone(warehouse_id)
    #         self.shipper_id = self.p_contract_id.partner_id and self.p_contract_id.partner_id.id or 0
    #
    # @api.model
    # @api.depends('move_ids','move_ids.state','move_ids.product_qty','move_ids.product_uom_qty')
    # def _get_avg_deduct(self):
    #     for stack in self:
    #         init_qty = stack.init_qty
    #         basis_qty = stack.remaining_qty
    #         if init_qty:
    #             stack.avg_deduction = (init_qty- basis_qty)*100 / init_qty
    #         else:
    #             stack.avg_deduction = 0.0
    #
    # avg_deduction = fields.Float(compute='_get_avg_deduct',digits=(16,3) , string = 'Avg Deduction')
    #
    # def dieuchinhqc(self):
    #     for this in self:
    #         this._compute_qc()
    #         return
    
