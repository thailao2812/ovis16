# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from odoo.exceptions import ValidationError, UserError

class StockPicking(models.Model):
    _inherit = "stock.picking"

    merge = fields.Boolean(string='Merge', default=False)
    
    def _get_printed_report_name(self):
        report_name = (_('%s')%(self.name))
        return report_name
    
    to_warehouse_id = fields.Many2one('stock.warehouse', string="To Warehouse")
    
    state_kcs = fields.Selection(
        selection=[('draft', 'New'), ('approved', 'Approved'), ('waiting', 'Waiting Another Operation'),
                   ('rejected', 'Rejected'), ('cancel', 'Cancel')], string='KCS Status', readonly=True, copy=False,
        index=True, default='draft', tracking=True, )
    
    backorder_id = fields.Many2one(
        'stock.picking', 'Back Order of',
        copy=False, index='btree_not_null', readonly=False,
        check_company=False,
        help="If this shipment was split, then this field links to the shipment which contains the already processed part.")
    
    @api.onchange('to_warehouse_id')
    def onchange_to_warehouse(self):
        if self.to_warehouse_id:
            self.location_id = self.warehouse_id.wh_input_stock_loc_id.id
            self.location_dest_id = self.picking_type_id.default_location_src_id.id
            for move in self.move_line_ids_without_package:
                move.location_id = self.location_id.id
                move.location_dest_id = self.location_dest_id.id
                    
    def create_picking_transfers(self):
        pick = self
        picking_type_id = pick.picking_type_id.transfer_picking_type_id
        if not picking_type_id:
            raise
        
        trans_id = self.env['stock.picking'].search([('backorder_id','=',pick.id)])
        if trans_id:
            action = self.env.ref('sd_inventory.action_tranfers_out_stock_good')
            result = action.read()[0]
            result['context'] = {}
            res = self.env.ref('stock.view_picking_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = trans_id.id or False
            return result
        
        if pick.origin:
            names = (pick.name) + '; '+ pick.origin
        else:
            names = (pick.name)
            
        new_id = pick.copy({'name':'/','picking_type_id':pick.picking_type_id.transfer_picking_type_id.id,
               'location_id':pick.picking_type_id.transfer_picking_type_id.default_location_src_id.id,
               'location_dest_id':pick.to_warehouse_id.wh_input_stock_loc_id.id, 
               'origin':names,
               'crop_id':pick.crop_id.id,
               'date_done':pick.date_done,
               'warehouse_id':pick.to_warehouse_id.id,
               'transfer':False,
               'move_line_ids_without_package':False,
               #'move_ids_without_package':False,
               'backorder_id':pick.id})
        
        for line in pick.move_line_ids_without_package:
            val ={
                'picking_id': new_id.id or False, 
                # 'name': name, 
                'product_uom_id': line.product_id.uom_id.id or False,
                'init_qty': 0.0, 
                'qty_done': 0.0, 
                'reserved_uom_qty':0.0,
                'price_unit': 0.0,
                'picking_type_id': new_id.picking_type_id.id or False,
                'location_id': new_id.location_id.id or False,
                'location_dest_id': new_id.location_dest_id.id or False,
                'company_id': self.env.user.company_id.id, 
                'zone_id':  False, 
                'product_id': line.product_id.id or False,
                'date': pick.date_done or False, 
                'currency_id': False,
                'state':'draft', 
                # 'warehouse_id': picking.warehouse_id.id or False,
                'lot_id':False,
                'packing_id':False,
                #'bag_no': 0
            }
            self.env['stock.move.line'].create(val)
        
        if new_id:
            action = self.env.ref('sd_inventory.action_tranfers_out_stock_good')
            result = action.read()[0]
            result['context'] = {}
            res = self.env.ref('stock.view_picking_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = new_id.id or False
            return result
        
        
        
    
    @api.onchange('backorder_id')
    def onchange_backorder_id(self):
        if self.picking_type_id.code == 'transfer_in':
            if self.backorder_id:
                self.origin = self.backorder_id.origin
                self.vehicle_no = self.backorder_id.vehicle_no
            else:
                self.origin = False
                self.vehicle_no = False
    
    barcode = fields.Char(string="Barcode")
    total_print_grn = fields.Integer('Print')
    note = fields.Text('Notes')
    delivery_order_id = fields.Many2one('delivery.order', string="Delivery order")
    
    def write(self, vals):
        #Kiet Cập nhật lại stock.move.line location khi thay đổi trên picking
        if vals.get('location_id', False):
            for i in self:
                for j in i.move_line_ids_without_package:
                    j.location_id = vals['location_id']
        
        if vals.get('location_dest_id', False):
            for i in self:
                for j in i.move_line_ids_without_package:
                    j.location_dest_id = vals['location_dest_id']

        return super(StockPicking, self).write(vals)
    
    
    @api.model
    def name_search(self, name ='', args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if self._context.get('back_order'):
            domain = [('picking_type_id.code','=','incoming'),
                      ('picking_type_id.operation','=','factory'),
                      ('partner_id', '=', self._context.get('partner_id')),
                      ('backorder_id', '=', False)]
            backorder = self.search(args + domain, limit=limit)
        else:
            backorder = self.search(args + domain, limit=limit)
        return backorder.name_get()
    
    def button_link_backorder(self):
        for pick in self:
            if pick.link_backorder_id:
                for old_backorder_id in self.env['stock.picking'].sudo().search([('backorder_id','=',pick.id)]):
                    if old_backorder_id.backorder_id:
                        old_backorder_id.origin = ''
                        old_backorder_id.backorder_id = 'null'

                names =''
                if pick.link_backorder_id.origin:
                    names = (pick.name) + '; '+ pick.link_backorder_id.origin
                else:
                    names = (pick.name)
                pick.link_backorder_id.backorder_id = pick.id
                pick.link_backorder_id.origin = names
        return
    
    @api.depends('backorder_id')
    def _compute_check_link_backorder(self):
        for this in self:
            if this.backorder_id:
                this.sudo().backorder_id.check_link_backorder = True
        return

    @api.onchange('warehouse_id')
    def onchange_domain_warehouse_id(self):
        # res = super(StockPicking, self).onchange_domain_warehouse_id()
        if self.env.context.get('material_in'):
            self.picking_type_id = self.env['stock.picking.type'].search([
                ('warehouse_id', '=', self.warehouse_id.id),
                ('code', '=', 'material_in')
            ], limit=1).id
        if self.env.context.get('material_out'):
            self.picking_type_id = self.env['stock.picking.type'].search([
                ('warehouse_id', '=', self.warehouse_id.id),
                ('code', '=', 'material_out')
            ], limit=1).id
        # return res
    
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('warehouse_id') and vals.get('picking_type_id'):
                if self.env.context.get('material_in'):
                    picking_type_id = self.env['stock.picking.type'].search([
                        ('warehouse_id', '=', vals.get('warehouse_id')),
                        ('code', '=', 'material_in')
                    ], limit=1).id
                    if vals.get('picking_type_id') != picking_type_id:
                        raise UserError(_("You can not change Picking Type"))
                if self.env.context.get('material_out'):
                    picking_type_id = self.env['stock.picking.type'].search([
                        ('warehouse_id', '=', vals.get('warehouse_id')),
                        ('code', '=', 'material_out')
                    ], limit=1).id
                    if vals.get('picking_type_id') != picking_type_id:
                        raise UserError(_("You can not change Picking Type"))
    
            if self.env.context.get('picking_type_id') and self.env.context.get('picking_type_id') == 'incoming':
                if vals.get('picking_type_id') and vals.get('location_id') and vals.get('location_dest_id'):
                    location_id = self.env['stock.picking.type'].search([
                        ('id', '=', vals.get('picking_type_id'))
                    ]).default_location_src_id.id
                    location_dest_id = self.env['stock.picking.type'].search([
                        ('id', '=', vals.get('picking_type_id'))
                    ]).default_location_dest_id.id
                    if vals.get('location_id') != location_id or vals.get('location_dest_id') != location_dest_id:
                        raise UserError(_("You cannot choose the Wrong Location and Destination"))
        
        picking_objs = super().create(vals_list)
        for pick in picking_objs:
            name = pick.name
            if pick.crop_id.short_name:
                crop = '-' + pick.crop_id.short_name +'-'
                name = name.replace("-", crop, 1)
                pick.name = name
        return picking_objs
    
    description_name = fields.Char(string='GRN FOT Name', default='GRN-FOT-', copy=False)

    @api.constrains('description_name')
    def unique_description_name_fot(self):
        for rec in self:
            if rec.picking_type_id.operation == 'station':
                check_fot_name = self.env['stock.picking'].search([
                    ('description_name', '=', rec.description_name.strip()),
                    ('id', '!=', rec.id),
                    ('picking_type_id.operation', '=', 'station')
                ])
                if check_fot_name:
                    raise UserError(_("You cannot create duplicate GRN-FOT Name, check again!!!"))
        return True
    
    
    @api.model
    def _default_crop_id(self):
        crop_ids = self.env['ned.crop'].search([('state', '=', 'current')], limit=1)
        return crop_ids
    
    rate_ptbf = fields.Float(string='Rate PTBF')
    
    crop_id = fields.Many2one('ned.crop', string='Crop', required=False, readonly=False, states={'draft': [('readonly', False)]}, default=_default_crop_id)
    
    @api.model
    def _domain_picking_type(self):
        return "[('id', 'in', %s)]" % self.env.user._picking_type_domain()

    picking_type_id = fields.Many2one(
        'stock.picking.type', string = 'Operation Type',
        required=True, readonly=True, index=True,
        domain=lambda self: self._domain_picking_type(),
        states={'draft': [('readonly', False)]})
    
    def button_validate(self):
        if self.picking_type_id.stack:
            move_no_stack = self.move_line_ids_without_package.filtered(lambda sa: sa.lot_id.id == False and sa.product_id.pass_kcs_for_loss == False)
            if move_no_stack:
                raise UserError(_("Stack / Lot can't be empty"))
        res = super().button_validate()
        return res
    
    def button_qc_assigned(self):
        for picking in self:
            picking.state ='assigned'
            name = picking.name
            if picking.picking_type_id.stack and picking.picking_type_id.code =='incoming':
                move_no_stack = self.move_line_ids_without_package.filtered(lambda sa: sa.lot_id.id == False)
                if move_no_stack:
                    raise UserError(_("Stack / Lot can't be empty"))
                
            if picking.date_done:
                picking.move_ids.write({'state': 'assigned','date':picking.date_done})
            else:
                picking.move_ids.write({'state': 'assigned'})
    
    
    def check_only_df(self):
        for pick in self:
            for line in pick.move_line_ids_without_package:
                df_pick = line.lot_id.move_line_ids.filtered(lambda x: x.picking_id.picking_type_id.code == 'phys_adj' and x.picking_id.id != pick.id and x.picking_id.state == 'done').mapped('picking_id')
                if line.lot_id.merge:
                    if len(df_pick) == 2:
                        raise UserError(_("You cannot Done this DF when stack merge have DF %s done in the history!! ") % (df_pick.name))
                else:
                    if df_pick:
                        raise UserError(_("You cannot Done this DF when stack have DF %s done in the history!! ") %(df_pick.name))
        return
            
    def button_sd_validate(self):
        for picking in self:
            if picking.picking_type_id.stack:
                move_no_stack = self.move_line_ids_without_package.filtered(lambda sa: sa.lot_id.id == False)
                if move_no_stack:
                    for check_loss in move_no_stack:
                        if check_loss.product_id.pass_kcs_for_loss == False:
                            raise UserError(_("Stack / Lot can't be empty"))
            
            if picking.picking_type_id.kcs and  picking.picking_type_id.kcs_approved == True:
                if picking.state_kcs != 'approved':
                    raise UserError(_("Picking make KCS done !!!"))
            
            #Kiểm tra các trường hợp lệnh sản xuất đã hoàn thành thì ko được done phiếu kho
            for finished in self.move_line_ids_without_package:
                if finished.finished_id.state =='done':
                    raise UserError(_("Production: %s completed, can't complete inventory") %(finished.finished_id.name))
            
            for material in self.move_line_ids_without_package:
                if material.material_id.state =='done':
                    raise UserError(_("Production %s :completed, can't complete inventory") %(material.material_id.name))
            
            if picking.picking_type_id.code == 'production_in':
                if picking.state_kcs != 'approved':
                    raise UserError(_("GRP %s can't complete inventory, QC Unapproved !!!") %(picking.name))
            
            picking.state ='done'
            if picking.state_kcs == 'waiting':
                picking.state_kcs = 'draft'
            picking.move_ids.write({'state': 'done'})
            picking.move_line_ids_without_package.write({'warehouse_id':picking.warehouse_id.id, 'date':picking.date_done})

            #Close phiếu DR khi done GRN tay
            picking.security_gate_id.state = 'closed'
            
            #Xừ lý dọn nhập hopper
            move_line_hopper = picking.move_line_ids_without_package.filtered(lambda r: r.zone_id.hopper == True or r.lot_id.zone_id.hopper == True)
            request_id = False
            if move_line_hopper and picking.picking_type_id.code =='incoming':
                for move in move_line_hopper:
                    if move.zone_id.hopper == True or move.lot_id.zone_id.hopper == True:
                        if not request_id:
                            val ={
                                  'name':'/',
                                  'origin':move.picking_id.name,
                                  'warehouse_id':move.picking_id.warehouse_id.id,
                                  'state':'draft'
                                }
                            request_id = self.env['request.materials'].create(val)
                        val ={
                                'product_id':move.product_id.id,
                                'product_uom':move.product_id.uom_id.id,
                                'product_qty':move.init_qty,
                                'stack_id':move.lot_id.id,
                                'request_id':request_id.id
                              }
                        self.env['request.materials.line'].create(val)
                        
            #Kiệt kiêm tra và sử lý không cho tạo nhiều DF ở trạng thái done
            if picking.picking_type_id.code == 'phys_adj':
                self.check_only_df()
            
            #Kiet bỏ vì sẽ ko còn empy stack trên stock.move.line
            # picking.create_adj_approved_picking()
            
    def _autoconfirm_picking(self):
        """ Automatically run `action_confirm` on `self` if the picking is an immediate transfer or
        if the picking is a planned transfer and one of its move was added after the initial
        call to `action_confirm`. Note that `action_confirm` will only work on draft moves.
        """
        #Kiet đè lại chỉ muốn tạo ra ở trạng thái draft thôi
        # Clean-up the context key to avoid forcing the creation of immediate transfers.
        return
    
    def btt_reopen_stock(self):
        for i in self:
            #Kiểm tra các trường hợp lệnh sản xuất đã hoàn thành thì ko được done phiếu kho
            for finished in i.move_line_ids_without_package:
                if finished.finished_id.state =='done':
                    raise UserError(_("Production: %s completed, can't complete inventory") %(finished.finished_id.name))
            
            for material in i.move_line_ids_without_package:
                if material.material_id.state =='done':
                    raise UserError(_("Production %s :completed, can't complete inventory") %(material.material_id.name))
                
            i.state = 'draft'
            for move in i.move_ids_without_package:
                move.state = 'draft'
            for move_line in i.move_line_ids_without_package:
                move_line.state = 'draft'
                if move_line.lot_id:
                    move_line.lot_id._get_remaining_qty()
            
    
    
    @api.model
    def default_get(self, fields):
        res = super(StockPicking, self).default_get(fields)
        picking_type = self.env['stock.picking.type']
        location = self.env['stock.location']
        
        location_transit_ids = [x.id for x in location.search([('usage','=','transit'),('active','=',True)])]
        if self._context.get('transfer_out'):
            picking_type_id = picking_type.search([('code','=','transfer_out'),('active','=',True)], limit=1)
        elif self._context.get('transfer_in'):
            picking_type_id = picking_type.search([('code','=','transfer_in'),('active','=',True)], limit=1)
        elif self._context.get('picking_internal'):
            picking_type_id = picking_type.search([('code','=','internal'),('active','=',True)], limit=1)
        elif self._context.get('picking_outgoing'):
            picking_type_id = picking_type.search([('code','=','outgoing'),('active','=',True)], limit=1)
        elif self._context.get('picking_return_supplier'):
            picking_type_id = picking_type.search([('code','=','return_supplier'),('active','=',True)], limit=1)
        
        elif self._context.get('picking_return_supplier'):
            picking_type_id = picking_type.search([('code','=','return_supplier'),('active','=',True)], limit=1)
            
        elif self._context.get('picking_grp_Goods'):
            picking_type_id = picking_type.search([('code','=','production_in'),('active','=',True)], limit=1)
            res.update({'domain': {'picking_type_id': picking_type_id.id}})
            
        elif self._context.get('picking_grn_Goods'):
            if self._context.get('fot'):
                picking_type_id = picking_type.search([('code','=','incoming'),('operation','=','station'),('active','=',True)], limit=1)
            else:
                picking_type_id = picking_type.search([('code','=','incoming'),('operation','=','factory'),('active','=',True)], limit=1)

        elif self._context.get('material_in'):
            picking_type_id = picking_type.search([('code','=','material_in'),('active','=',True)], limit=1)
        elif self._context.get('material_out'):
            picking_type_id = picking_type.search([('code','=','material_out'),('active','=',True)], limit=1)

        else:
            picking_type_id = picking_type.search([('active','=',True)], limit=1)
            
        res['picking_type_id'] = picking_type_id.id
        res['picking_type_code'] = picking_type_id.code
        return res
    
    is_quota_temp = fields.Boolean(string='Is Quota Temp')
    
    
    
    def _default_warehouse(self):
        warehouse_ids = self.env['stock.warehouse'].with_context(user_workers=True).search(
            [('company_id', '=', self.env.user.company_id.id)])
        # default with user only working 1 company account analytic
        if warehouse_ids:
            return warehouse_ids[0]
    
    @api.model
    def _domain_warehouse(self):
        return "[('id', 'in', %s)]" % self.env.user._warehouses_domain()
        
    warehouse_id = fields.Many2one('stock.warehouse',string="Warehouse", default=_default_warehouse, domain=lambda self: self._domain_warehouse())
    categ_id = fields.Many2one(related='product_id.categ_id',  string='Product Category',store = True)
    #Kiet dieu chỉnh để có thể nhập thông tin date done
    date_done = fields.Datetime('Date of Transfer', copy=False, readonly=False, help="Date at which the transfer has been processed or cancelled.", 
                                states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},)
    
    #Besco Contract
    sale_contract_id = fields.Many2one('sale.contract', string='Sale Contract',  ondelete='cascade', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},)
    delivery_id = fields.Many2one('delivery.order', string='Delivery Order', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},)
    
    #NEd Contract
    cert_type = fields.Selection([('normal', 'Normal'), ('quota', 'Quota')], string='Certificate type', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},)
    pcontract_id = fields.Many2one('s.contract', string='Purchase Contract',states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},)
    
    grn_id = fields.Many2one('stock.picking', string='GRN',states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},)
    delivery_place_id = fields.Many2one('delivery.place', string='Delivery Place',
       readonly=True, states={'draft': [('readonly', False)]}, required=False,)
    
    #NED Stock
    # delivery_fee = fields.One2many('delivery.fee','picking_id', string='Delivery Fee',)
    vehicle_no = fields.Char(string='Vehicle No.', required=False, size=128, states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},)
    transfer = fields.Boolean(string='Transfer',default= False, states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},)
    
    lot_id = fields.Many2one(related='move_line_ids_without_package.lot_id',  string='Stack',store = True , tracking=True)
    init_lot = fields.Float(string='Stack Qty', related='lot_id.init_qty', store=True)
    zone_id = fields.Many2one(related='move_line_ids_without_package.zone_id',  string='Zone',store = True, tracking=True)
    packing_id = fields.Many2one(related='move_line_ids_without_package.packing_id',  string='Packing', store= True, tracking=True)
    reweighing_reason = fields.Text(related='move_line_ids_without_package.description_picking',  string='Reweighing Reason',store = True , tracking=True)
    first_weight = fields.Float(related='move_line_ids_without_package.first_weight',  string='First Weight',store = True , tracking=True)
    second_weight = fields.Float(related='move_line_ids_without_package.second_weight',  string='Second Weight',store = True , tracking=True)
    
    certificate_id = fields.Many2one('ned.certificate', string='Certificate', ondelete='restrict', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},)
    districts_id = fields.Many2one('res.district', string='Source', ondelete='restrict', required=False, states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},)
    # move_weight = fields.One2many('stock.move','picking_id', string='Weighing',)
    product_id = fields.Many2one('product.product', 'Product', related='move_line_ids_without_package.product_id', readonly=True, store = True, tracking=True)
    
    pledg = fields.Char(string='Pledging', required=False, size=128)
    
    to_picking_type_id =fields.Many2one('stock.picking.type',  string='To Warehouse',copy=False)
    
    production_id = fields.Many2one('mrp.production', string='Manufacturing Orders')
    
    picking_type_code = fields.Selection(related="picking_type_id.code", string="Picking Type Code", store = True)
    
    
    # picking_type_code = fields.Selection(selection_add=[('material_in','Material In'),('material_out','Material Out'),('adjust_stock','Adjust stock')])
    # purchase_order_id =fields.Many2one('purchase.order', string='Purchase Note',copy=False)
    
    @api.depends('move_line_ids_without_package.qty_done',
                'move_line_ids_without_package',
                'move_line_ids_without_package.init_qty',
                'move_line_ids_without_package.bag_no',
                'move_line_ids_without_package.picking_id.state')
    def _total_qty(self):
        for order in self:
            total_qty = total_bag = total_weighbridge_qty = total_init_qty = 0
            for line in order.move_line_ids_without_package:
                total_qty +=line.qty_done or 0.0 
                total_init_qty +=line.init_qty or 0.0
                total_weighbridge_qty += line.weighbridge or 0.0
                total_bag += line.bag_no
                
            order.total_qty = total_qty
            order.total_init_qty = total_init_qty or 0.0
            order.total_bag = total_bag or 0.0
            order.total_weighbridge_qty = total_weighbridge_qty or 0.0
            
            
    total_qty = fields.Float(compute='_total_qty',digits=(16,0) , string = 'Total Qty',store=True, tracking=True)
    total_init_qty = fields.Float(compute='_total_qty',digits=(16,0) , string = 'Init Qty',store=True, tracking=True)
    total_weighbridge_qty = fields.Float(compute='_total_qty',digits=(16,0) , string = 'Real Qty',store=True, tracking=True)
    
    weight_scale_id = fields.Char(string='Weight Scale No.')
    total_bag = fields.Float(compute='_total_qty',digits=(16,0) , string = 'Bag',store=True, tracking=True)
    
#     product_name = fields.Char(related='product_id.name_template', string="Product Name")
#     product_id = fields.Many2one(related ='move_lines.product_id' ,relation ='product.product',string='Product',store = True)
    #security_gate_que_ue
    trucking_id = fields.Many2one('res.partner', string='Trucking Co')
    
    #NED Purchase Contract
    # cert_type = fields.Selection([('normal', 'Normal'), ('quota', 'Quota')], string='Certificate type')
    # pcontract_id = fields.Many2one('s.contract', string='Purchase Contract')
    
    def _action_done(self):
        date_done = self.date_done
        res = super()._action_done()
        self.write({'date_done': date_done})
        #:Kiet Nghiệp vụ nhập hàng vào hopper hệ thống tự động tạo ra 1 phiếu request
        move_line_hopper = self.move_line_ids_without_package.filtered(lambda r: r.zone_id.hopper == True or r.lot_id.zone_id.hopper == True)
        request_id = False
        if move_line_hopper and self.picking_type_id.code =='incoming':
            for move in move_line_hopper:
                if move.zone_id.hopper == True or move.lot_id.zone_id.hopper == True:
                    if not request_id:
                        val ={
                              'name':'/',
                              'origin':move.picking_id.name,
                              'warehouse_id':move.picking_id.warehouse_id.id,
                              'state':'draft'
                            }
                        request_id = self.env['request.materials'].create(val)
                    val ={
                            'product_id':move.product_id.id,
                            'product_uom':move.product_id.uom_id.id,
                            'product_qty':move.init_qty,
                            'stack_id':move.lot_id.id,
                            'request_id':request_id.id
                          }
                    self.env['request.materials.line'].create(val)
        return res
        
    
    
    