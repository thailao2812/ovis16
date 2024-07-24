from operator import attrgetter
from re import findall as regex_findall, split as regex_split

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
import datetime
from odoo.tools import float_round


class StockLot(models.Model):
    _inherit = 'stock.lot'
    _order = 'name, id'
    
    
    def action_lock_stock_lot(self):
        for i in self:
            i.lock =True
    
    def action_unlock_stock_lot(self):
        for i in self:
            i.lock =False
    
    def print_summary_stack(self):
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'report_summary_stack',
        }
    
    def _get_printed_report_name(self):
        return (_('%s')%(self.name))
    
            
    def print_summary_stack(self):
        return self.env.ref(
            'sd_inventory.report_summary_stack').report_action(self)
    
    stack_type = fields.Selection([
        ('pallet', 'Pallet'),
        ('stacked', 'Stacked'),
        ('pile', 'Pile'),
        ('jum_1', 'Jum-1.0'),
        ('jum_1_3', 'Jum-1.3'),
        ('jum_1_5', 'Jum-1.5'),
        ('stack_wip', 'Stack Wip'),
        ('hp', 'Hopper')
    ],
    string='Stack type', default='stacked')
    
    name = fields.Char(
        'Lot/Stack', default= '/',
        required=True, help="Unique Lot/Serial Number", index='trigram')
    
    code = fields.Char(string='Code')
    province_id = fields.Many2one('res.country.state','Province',)
    delivery_place_id = fields.Many2one('delivery.place','Delivery Place')
    lock = fields.Boolean(string='Lock',default = False, tracking=True)
    p_contract_id = fields.Many2one('s.contract', string='P Contract')
    zone_id = fields.Many2one('stock.zone', string='Zone',  ondelete='cascade',  copy=False)
    active = fields.Boolean(string='Active',default = True,)
    districts_id = fields.Many2one('res.district', string='Source', ondelete='restrict')
    date = fields.Date(string="Date")
    # picking_id = fields.Many2one(related ='move_ids.picking_id',  string='Picking',store=True)
    
    pledged = fields.Char(string="Pledged.")
    warehouse_id = fields.Many2one(related='zone_id.warehouse_id',  string='Warehouse',store = True)
    stack_empty = fields.Boolean('Stack empty', default = False)
    shipper_id = fields.Many2one(related="p_contract_id.partner_id",store = True, string='Shipper')
    certificate_id = fields.Many2one(related="p_contract_id.certificate_id",store = True, string='Certificate')
    bag_out = fields.Float(string="Bag Ex")
    p_qty = fields.Float(string="Ctr.Qty (Kg)")
    wr = fields.Float(string="WR")
    unreceived = fields.Float(string="Unreceived")
    
    move_line_ids = fields.One2many('stock.move.line','lot_id',string="Move Line")
    
    stack_wip = fields.Boolean(string='Stack wip', default= False)
    
    # product_id = fields.Many2one(related='move_line_ids.product_id',  string='Product',store=True)
    categ_id = fields.Many2one(related='product_id.categ_id',  string='Category',store=True)
    
    allocate_qty = fields.Float(string='Allocated Qty', compute='_compute_allocated_qty')
    stack_on_hand = fields.Char(string='Real Stack Export')
    
    bag_qty = fields.Float(compute='_get_remaining_qty',  string='Bag',store=True, digits=(12, 0),)
    stack_qty = fields.Float(compute='_get_remaining_qty',  string='Basis Weight',store=True, digits=(12, 0),)
    init_qty = fields.Float(compute='_get_remaining_qty',  string='Net Weight',store=True, digits=(12, 0),)
    out_qty = fields.Float(string='Ex Weight', digits=(12, 0))
    remaining_qty = fields.Float(compute='_get_remaining_qty',  string='Remain Weight', digits=(12, 0), store=True,)
    init_invetory = fields.Boolean(string="init_invetory", default = False, copy = False)
    init_invetory_qty = fields.Float(string="Init Invetory Qty")
    init_invetory_bags = fields.Float(string="Init Invetory Bags")
    reason_stack_empty = fields.Text(string="Reason Stack empty")
    stack_his_ids = fields.Many2many('stock.stack.transfer', 'transfer_stack_rel', 'lot_id', 'transfer_id', string='Stack', readonly=True,)
    merge = fields.Boolean(string='Stack Merged', default=False)
    parent_id = fields.Many2one('stock.lot')
    stock_lot_history_ids = fields.One2many('stock.lot', 'parent_id', string='History Lot')
    
    
    # @api.constrains('init_qty')
    # def _contrains_init_qty(self):
    #     for obj in self:
    #         if obj.init_qty <0:
    #             raise ValidationError(_('Balance Qty> 0'))
    
    def write(self, vals):
        lot = super(StockLot, self).write(vals)
        if self.p_contract_id:
            self.p_contract_id.wr_line = self.id
        else:
            self.p_contract_id.wr_line = False
        return lot
    
    @api.model
    def create(self, vals):
        if vals.get('name',False) == '/':
            if vals.get('zone_id',False):
                zone = self.env['stock.zone'].browse(vals['zone_id'])
                if zone.hopper:
                    vals['name'] = self.env['ir.sequence'].next_by_code('stock.stack.hopper.seq') or 'New'
                elif zone.location_wip:
                    vals['name'] = self.env['ir.sequence'].next_by_code('stock.stack.wip.seq') or 'New'
                else:
                    vals['name'] = self.env['ir.sequence'].next_by_code('stock.sack.seq') or 'New'
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('stock.sack.seq') or 'New'
                
        if vals.get('date',False) == False:
            # vals['date'] =  time.strftime(DATE_FORMAT)
            vals['date'] = datetime.date.today()
        result = super(StockLot, self).create(vals)
        
        #Thai dim. ko cho phép tạo mới stack từ các hoạt động ko liên quan tới kho
        # if 'p_contract_id' in vals:
        #     self.env['s.contract'].browse(vals['p_contract_id']).write({'wr_line': result.id})
        return result
    
    
    def unlink(self):
        for record in self:
            for line in record.qc_line_ids:
                line.unlink()
            if record.move_line_ids:
                raise UserError(_('You can not delete Stack'))
        return super(StockLot, self).unlink()
    
    @api.constrains('name')
    def _check_name_duplicate(self):
        #Kiet: check duplicate Code (Stack)
        if self.name:
            e_ids = self.search([('id','!=',self.id),('name','=',self.name)])
            if len(e_ids):
                raise UserError(("name '%s' is already exist for Stack '%s'!")%(self.name, self.name)) 
    

    def _compute_allocated_qty(self):
        for i in self:
            sale_contract_detail_draft = self.env['sale.contract.deatail'].search([
                ('stack_id', '=', i.id),
                ('sp_id', '!=', False)
            ])
            if sale_contract_detail_draft:
                i.allocate_qty = sum(detail.tobe_qty for detail in sale_contract_detail_draft)
            else:
                i.allocate_qty = 0
    
    @api.model
    @api.depends('move_line_ids','move_line_ids.picking_id.state','move_line_ids.qty_done')
    def _get_avg_deduct(self):
        for stack in self:
            init_qty = stack.init_qty
            basis_qty = stack.remaining_qty
            if init_qty:
                stack.avg_deduction = (init_qty- basis_qty)*100 / init_qty
            else:
                stack.avg_deduction = 0.0
            
    avg_deduction = fields.Float(compute='_get_avg_deduct',digits=(16,3) , string = 'Avg Deduction')
    
    def create_picking_adj(self):
        if self.stack_empty == True:
            return
        if self.init_qty ==0:
            return
        if self.reason_stack_empty == False:
            self.reason_stack_empty = 'Adjustment Stack'
            # error = "Nhập lý do Hủy Stack"
            # raise UserError(_(error))
        
        warehouse_obj = self.warehouse_id
        company_id = warehouse_obj.company_id.id or False
        move_line = self.env['stock.move.line']
        # operation_produce = self.env['mrp.production.workcenter.product.produce']
        # operation_consumed = self.env['mrp.production.workcenter.consumed.produce']
     
        picking_type_id = warehouse_obj.adj_type_id or False
        if not picking_type_id.default_location_src_id:
            error = "Locations  does not exist."
            raise UserError(_(error))
        location_id = picking_type_id.default_location_src_id
        
        if not picking_type_id.default_location_dest_id.id:
            error = "Location Destination does not exist."
            raise UserError(_(error))
        location_dest_id = picking_type_id.default_location_dest_id
        
        intenal_location_id = warehouse_obj.lot_stock_id
        
        location_id = self.init_qty > 0 and intenal_location_id or picking_type_id.default_location_src_id
        location_dest_id = self.init_qty > 0 and picking_type_id.default_location_dest_id or intenal_location_id
        
        # Kiệt: Create nhập kho Thành phẩm Thêm Picking để KCS Sucden
        var = {
            'warehouse_id':warehouse_obj.id,
            'name': '/',
            'picking_type_id': picking_type_id.id,
            'partner_id': False,
            'date': fields.Datetime.now(),
            'date_done':fields.Datetime.now(),
            # 'date_sent': fields.Datetime.now(),
            # 'origin': produced.pending_grn or False,
            'location_dest_id':  location_dest_id.id,
            'location_id': location_id.id,
            'state':'draft',
            # 'production_id':production_obj.id,
            # 'operation_id':result.operation_id.id,
            # 'result_id':result.id,
            'note': self.reason_stack_empty or 'Điều chỉnh Stack'
        }
        picking_id = self.env['stock.picking'].create(var)
        move_line.create({'picking_id': picking_id.id, 
                          # 'name': produced.product_id.name or '', 
                        'product_id': self.product_id.id or False,
                        'product_uom_id': self.product_id.uom_id.id or False, 
                        'init_qty':self.init_qty or 0.0, 
                        'weighbridge':self.init_qty or 0.0, 
                        'qty_done': self.init_qty or 0.0, 
                        #'price_unit': 0.0,
                        'picking_type_id': picking_type_id.id or False, 
                        'location_id': location_id.id or False, 
                        # 'production_id': production_obj.id,
                        'location_dest_id': location_dest_id.id or False, 
                        'date': picking_id.date_done, 
                        
                        'lot_id': self.id,
                        
                        'zone_id':self.zone_id and self.zone_id.id or False,
                        'packing_id':self.packing_id.id,
                        'bag_no':self.bag_qty or 0.0,
                        'company_id': company_id, 
                        'state':'draft', 
                        # 'scrapped': False, 
                        'warehouse_id': warehouse_obj.id or False,
                        #Lien kết vối lệnh sản xuất
                        })
        picking_id.button_qc_assigned()
        self.stack_empty = True
             
        return
    
    def change_product(self):
        if self.move_line_ids:
            for move in self.move_line_ids:
                move.action_cancel()
                move.product_id = self.product_change_id.id
                move.picking_id.product_id = self.product_change_id.id
                move.action_done()
        #Change product for QC Picking
            sql = '''
                UPDATE request_kcs_line set product_id = %s
                WHERE stack_id = %s
            '''%(self.product_change_id.id,self.id)
            self.env.cr.execute(sql)
            # print sql
            # print self.env.cr.execute(sql)

    product_change_id = fields.Many2one('product.product', string='Change Product')
    
    
    @api.model
    @api.depends('shipment_id')
    def _get_out_qty(self):
        shipping_obj = self.env['shipping.instruction']
        for record in self:
            total_qty = 0
            for ship in record.shipment_id:
                shiping_info = shipping_obj.browse(ship.id)
            record.out_qty = total_qty
            
    
    def compute_qty(self):
        self._get_remaining_qty()
        self._compute_qc()
        
    @api.model
    @api.depends('move_line_ids', 'move_line_ids.picking_id.state', 'move_line_ids.qty_done','move_line_ids.bag_no', 'move_line_ids.location_id',
                 'move_line_ids.location_dest_id', 'stack_empty', 'is_bonded', 'out_qty','move_line_ids.state', 'init_invetory_qty','init_invetory_bags','init_invetory')
    def _get_remaining_qty(self):
        uom_obj = self.env['uom.uom']
        for stack in self:
            stack_qty = remaining_qty = 0.0
            # rounding = 0.0
            init = 0.0
            bag_qty = 0
            #Số init tồn khokho
            if stack.init_invetory == True:
                init += stack.init_invetory_qty or 0.0
                bag_qty += stack.init_invetory_bags or 0.0
                remaining_qty += stack.init_invetory_qty
                
            for move_line in stack.move_line_ids.filtered(lambda x: x.state == 'done'):
                print(move_line.picking_id.name)
                qty = move_line.init_qty
                init_qty = move_line.init_qty
                # rounding = move_line.product_id.uom_id.rounding
                # Kiet: nhap kho
                if move_line.location_dest_id.usage in ('internal') and move_line.location_id.usage not in ('internal') and move_line.state == 'done':
                    remaining_qty += qty
                    stack_qty += qty
                    init += init_qty
                    bag_qty += move_line.bag_no
                
                #Kiệt xuất kho
                if move_line.location_id.usage in ('internal') and move_line.location_dest_id.usage not in ('internal')  and move_line.state == 'done':
                    # kiet: Trừ dòng xuất tiêu thụ ra vì đã trừ rồi
                    remaining_qty -= qty
                    init -= init_qty
                    bag_qty -= move_line.bag_no or 0.0
                
                if move_line.location_id.usage in ('internal') and move_line.location_dest_id.usage in ('internal')  and move_line.state == 'done' and move_line.picking_id.picking_type_id.code =='production_out':
                    # kiet: Trừ dòng xuất tiêu thụ ra vì đã trừ rồi
                    remaining_qty -= qty
                    init -= init_qty
                    bag_qty -= move_line.bag_no or 0.0
                
                #Kiet xuất kho từ NVP -> HCM internal qua Internal
                if move_line.location_dest_id.usage in ('internal') and move_line.location_id.usage in ( 'internal') and move_line.state == 'done' and move_line.picking_id.picking_type_id.code =='outgoing':
                    remaining_qty -= qty
                    init -= init_qty
                    bag_qty -= move_line.bag_no or 0.0
                
                #Kiet dim lại sẽ ko cho xuất hiện nghiệp vụ internal wa internal
                # if move_line.location_dest_id.usage in ('internal') and move_line.location_id.usage in ('internal') and move_line.state == 'done':
                #     remaining_qty -= qty
                #     init -= init_qty
                #     bag_qty -= move_line.bag_no or 0.0

            # if stack.is_bonded and stack.qc_line_ids:
            #     print stack.is_bonded, stack.qc_line_ids
            #     print 'here'
            #     stack.init_qty = stack.qc_line_ids[0].instored
            #     print stack.out_qty
            #     print stack.qc_line_ids[0].instored
            #     stack.remaining_qty = stack.qc_line_ids[0].instored - stack.out_qty
            # else:
            # if stack.stack_empty:
            #     stack.init_qty = 0
            #     stack.remaining_qty = 0
            #     stack.bag_qty = 0
            # else:
            if init < 0:
                raise ValidationError(_('Stack %s must Balance Qty > 0') %(stack.name))
            
            stack.init_qty = init
            stack.remaining_qty = remaining_qty
            stack.stack_qty = stack_qty
            stack.bag_qty = bag_qty
    
    
    
    ########################## 24/04/2023 ###############################
    stack_processing_loss = fields.Boolean('Stack Processing Loss', default = False)
    state_id = fields.Many2one('res.country.state', string='State')
    currency_id = fields.Many2one('res.currency', string='Currency')
    
    
    bank_id = fields.Many2one('res.bank', string='Banks', readonly=True)
    mortgage_amount = fields.Float(string='Amount',readonly=True, )
    currency_id = fields.Many2one('res.currency', string='Currency')
    limit_qty = fields.Float(string='Limit Qty',digits=(12, 0))
    production_id = fields.Many2one('mrp.production', string='Manufacturing Orders')
    contract_id = fields.Many2one('s.contract', string='SNo.')
    districts_id = fields.Many2one('res.district', string='Source', ondelete='restrict')
    picking_id = fields.Many2one(related ='move_line_ids.picking_id',  string='Picking',store=True)
    pledged = fields.Char(string="Pledged.")
    # warehouse_id = fields.Many2one(related='zone_id.warehouse_id',  string='Warehouse',store = True)
    # is_bonded = fields.Boolean(string='Is Bonded')
    # stack_empty = fields.Boolean('Stack empty', default = False)
    # shipper_id = fields.Many2one('res.partner', string='Shipper')
    
    # total_allocation = fields.Float(digits=(16,0) , string = 'Allocation Qty',store=True)
    # total_remain = fields.Float(digits=(16,0) , string = 'Remain Qty',store=True)
    greatersc12_count = fields.Char(string="greatersc12_count")
    doc_weight = fields.Char(string="Doc Weight")
    # x_inspectator = fields.Many2one('x_inspectors.kcs', string='Inspectors')
    x_in_qty  = fields.Float(string = 'X in Qty')
    x_bag_in = fields.Float(string = 'X Bag In')
    x_bag_out = fields.Float(string = 'X Bag Out')
    stack_on_hand_moved0 = fields.Float(string = 'X Bag Out')
    is_bonded = fields.Boolean(string='Is Bonded')
    
    @api.depends('date')
    def _compute_date(self):
        for line in self:
            if line.date:
                line.year_tz = line.date.year
            else:
                line.year_tz = False

    year_tz = fields.Char(compute='_compute_date',string = "Year", store=True)

    allocation_npe_ids = fields.One2many('stack.nvp.relation', 'stack_id' ,'Allocation NPE',)

    @api.depends('allocation_npe_ids', 'allocation_npe_ids.product_qty')
    def _total_qty(self):
        for order in self:
            total_allocation = 0
            for line in order.allocation_npe_ids:
                total_allocation += line.product_qty
            order.total_allocation = total_allocation
            order.total_remain = order.remaining_qty - total_allocation

    total_allocation = fields.Float(compute='_total_qty', digits=(16, 0), string='Allocation Qty', store=True)
    total_remain = fields.Float(compute='_total_qty', digits=(16, 0), string='Remain Qty', store=True)


class StackNvpRelation(models.Model):
    _name = "stack.nvp.relation"

    # @api.depends('stack_id', 'contract_id')
    # def _origin_qty(self):
    #     for this in self:
    #         origin_qty = 0.0
    #         if this.stack_id:
    #             for line in this.stack_id.stack_line:
    #                 origin_qty += line.product_qty
    #             this.origin_qty = origin_qty

    stack_id = fields.Many2one('stock.stack', string='Stack')
    contract_id = fields.Many2one('purchase.contract', string='NPE')
    product_qty = fields.Float('Qty Allocation', digits=(16, 0))
    # origin_qty = fields.Float(compute='_origin_qty',string = 'Original Qty',digits=(16, 0))
    
    
