# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

class ShippingInstruction(models.Model):
    _name = "shipping.instruction"
    _order = 'create_date desc, id desc'
    _description = "Shipping Instruction"
            
    #invoice_count = fields.Integer(compute='_compute_invoices', string='Receptions', default=0)
    #invoice_ids = fields.One2many('account.invoice', 'si_id', string='Invoiced List', readonly=True, copy=False)
    
    def print_commercial_invoice(self):
        return 
    
    def print_trucking_list(self):
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'trucking_list_report',
        }
    
    @api.model
    def _default_crop_id(self):
        crop_ids = self.env['ned.crop'].search([('state', '=', 'current')], limit=1)
        return crop_ids
    
    
    crop_id = fields.Many2one('ned.crop', string='Crop', required=False, default=_default_crop_id)
    
    
    def create_invoice(self):
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('sd_sale_contract.action_wizard_invoice')
        form_view_id = imd.xmlid_to_res_id('sd_sale_contract.view_wizard_invoice')
    
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[form_view_id, 'form']],
            'target': action.target,
            'res_model': action.res_model,
            }
        return result
    
    @api.model
    def _default_warehouse_id(self):
        company = self.env.user.company_id.id
        warehouse_ids = self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1)
        return warehouse_ids
    
    @api.model
    def _default_shipment_from(self):
        company = self.env.user.company_id.id
        warehouse_id = self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1)
        return warehouse_id.partner_id.id
    
    @api.depends('contract_ids')
    def _compute_contracts(self):
        for ship in self:
            ship.contract_count = len(ship.contract_ids)
    
    @api.depends('invoice_ids')
    def _compute_invoices(self):
        for contract in self:
            contract.invoice_count = len(contract.invoice_ids)
            
    @api.depends('shipping_ids','shipping_ids.product_qty')
    def _compute_line_qty(self):
        for ship in self:
            total_qty = 0.0
            for ship_line in ship.shipping_ids:
                total_qty += ship_line.product_qty 
            ship.total_line_qty = total_qty
    
    @api.depends('containers_ids','containers_ids.product_qty')
    def _compute_cont_qty(self):
        for ship in self:
            total_qty = 0.0
            for containers in ship.containers_ids:
                total_qty += containers.product_qty 
            ship.total_cont_qty = total_qty
    
    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True, default='New')
    contract_id = fields.Many2one('s.contract', string='S Contract No.', ondelete='cascade', readonly=True, copy=False, states={'draft': [('readonly', False)]})
    sequence = fields.Integer(string='Sequence', default=10, states={'draft': [('readonly', False)]})
    date = fields.Date(string='Date', readonly=True, index=True, states={'draft': [('readonly', False)]}, default=fields.Datetime.now,change_default=True,)
    deadline = fields.Date(string='Deadline', required=True, readonly=True, states={'draft': [('readonly', False)]}, default=fields.Datetime.now,)

    company_id = fields.Many2one('res.company', string='Company', required=True, change_default=True, readonly=True, states={'draft': [('readonly', False)]}, default=lambda self: self.env['res.company']._company_default_get('shipping.instruction'))
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=True, readonly=True, states={'draft': [('readonly', False)]}, default=_default_warehouse_id)
    
    state = fields.Selection([('draft', 'New'),('waiting','Waiting Approve'),('approved', 'Approved'),('done', 'Done'),('cancel', 'Cancelled')],
             string='Status', readonly=True, copy=False, index=True, default='draft')
    
    note = fields.Text('Terms and conditions')
    origin = fields.Char(string='Source Document')

    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True, states={'draft': [('readonly', False)]}, required=False, index=True)
    
    create_date = fields.Date(string='Creation Date', readonly=True, index=True, default=fields.Datetime.now)
    create_uid = fields.Many2one('res.users', 'Responsible', readonly=True , default=lambda self: self._uid)
    date_confirm = fields.Date('Date Confirmed', readonly=True,  copy=False)
    user_confirm = fields.Many2one('res.users', string='User Confirm', readonly=True)
    date_approve = fields.Date('Approval Date', readonly=True,  copy=False)
    user_approve = fields.Many2one('res.users', string='User Approve', readonly=True)
    
    shipping_line = fields.Many2one('res.partner', string='Shipping Line', copy=False, readonly=False,
            states={'draft': [('readonly', False)], 'waiting': [('readonly', False)]}, index=True, domain=[('transfer', '=', True)])
    forwarding_agent = fields.Char(string='Forwarding Agent', copy=False, readonly=True,
            states={'draft': [('readonly', False)], 'waiting': [('readonly', False)]}, index=True,size=128)
    
    
    port_of_loading = fields.Many2one('delivery.place', string='Port Of Loading', copy=False, readonly=True,  states={'draft': [('readonly', False)], 'waiting': [('readonly', False)]}, index=True)
    port_of_discharge = fields.Many2one('delivery.place', string='Port of Discharge', copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True)
    container_status = fields.Selection([('fcl/fcl', 'FCL/FCL'), ('lcl/fcl', 'LCL/FCL'), ('lcl/lcl', 'LCL/LCL')], string='Container Status', readonly=True, 
                                         states={'draft': [('readonly', False)], 'waiting': [('readonly', False)]}, copy=False, index=True)
                                        
    factory_etd = fields.Date('Factory ETD', copy=False, readonly=True,  states={'draft': [('readonly', False)], 'waiting': [('readonly', False)]}, index=True)
    push_off_etd = fields.Date('Push off ETD', copy=False, readonly=True,  states={'draft': [('readonly', False)], 'waiting': [('readonly', False)]}, index=True)

    booking_ref_no = fields.Char(string='Booking No./ BL No.', index=True)
    booking_date = fields.Date('Booking date', copy=False, readonly=True,  states={'draft': [('readonly', False)], 'waiting': [('readonly', False)]}, index=True)
    reach_date = fields.Date('Reach Date', copy=False, readonly=True,  states={'draft': [('readonly', False)], 'waiting': [('readonly', False)]}, index=True)
    ico_permit_no = fields.Char(string='ICO No.', copy=False, readonly=True,  states={'draft': [('readonly', False)], 'waiting': [('readonly', False)]}, index=True)
    ico_permit_date = fields.Date('ICO Permit Date', readonly=True,  states={'draft': [('readonly', False)], 'waiting': [('readonly', False)]}, index=True)
    transaction = fields.Char(string='Transaction', copy=False, readonly=True,  states={'draft': [('readonly', False)], 'waiting': [('readonly', False)]}, index=True)
    vessel_flight_no = fields.Char(string='Vessel/Flight No.', copy=False, readonly=True,  states={'draft': [('readonly', False)], 'waiting': [('readonly', False)]}, index=True)
    
    shipping_ids = fields.One2many('shipping.instruction.line', 'shipping_id', string=' Shipping Instruction Lines', readonly=True,
                                                    copy=False, states={'draft': [('readonly', False)]}, )
    containers_ids = fields.One2many('bes.containers', 'shipping_id', string=' Container Details', readonly=True, copy=False,  states={'draft': [('readonly', False)], 'waiting': [('readonly', False)]})
    
    incoterms_id = fields.Many2one('account.incoterms',string='Incoterms',  readonly=True,  states={'draft': [('readonly', False)], 'waiting': [('readonly', False)]}, index=True)
    
    contract_count = fields.Integer(compute='_compute_contracts', string='Receptions', default=0)
    contract_ids = fields.One2many('sale.contract', 'shipping_id', string='Sale Contract', readonly=True, copy=False)
    
    
    type_of_stuffing = fields.Text(string="Type Of Stuffing",  states={'draft': [('readonly', False)], 'waiting': [('readonly', False)]})
    marking = fields.Text(string="Marking",  states={'draft': [('readonly', False)], 'waiting': [('readonly', False)]})
    
    total_line_qty = fields.Float(compute='_compute_line_qty', string='Qty', default=0, store= True)
    total_cont_qty = fields.Float(compute='_compute_cont_qty', string='Total Qty', default=0, store= True)
    
    product_id = fields.Many2one(related = 'shipping_ids.product_id',  string='Product', store = True)
    
    #Erro
    client_ref = fields.Char(related = 'contract_id.client_ref', string="Client ref.")
    number_of_container = fields.Integer(string="Number Of Container")
    reference = fields.Char(string='Commercial Reference Number')
    # client_ref = fields.Char(string="Client ref.") Integer
    ################################################################################################################################################
    @api.onchange('contract_id')
    def onchange_scontract_id(self):
        for record in self:
            if record.contract_id:
                record.s_ids = [record.contract_id.id]
    
    @api.depends('contract_ids.total_qty','contract_ids')
    def _allocated_qty(self):
        for order in self:
            allocated_qty = 0
            #eroo
            # for nvs in order.contract_ids:
            #     allocated_qty += nvs.total_qty
            order.allocated = allocated_qty

    @api.depends('contract_id')
    def get_allocated_s(self):
        for record in self:
            if record.contract_id:
                record.s_ids = [record.contract_id.id]

    @api.depends('allocation_ids')
    def get_allocated_p(self):
        for record in self:
            if record.allocation_ids:
                try:
                    record.p_allocated_ids = ', '.join([p.contract_p_id.name for p in record.allocation_ids])
                    record.p_ids = [p.contract_p_id.id for p in record.allocation_ids]
                except:
                    pass

    def split_shipment(self):
        new_record = 0
        for record in self:
            return {
                'name': 'Split Shipment',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'shipping.split',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': {'default_shipment_id': record.id},
            }
    
    
    
    x_link_id = fields.Many2one(related='contract_id.traffic_link_id',  string='Traffic Linked')
    
    # allocated = fields.Float(compute='_allocated_qty', string='Allocated', store=False, digits=(12, 0))
    
    prodcompleted = fields.Date(string="Prod. completion est.",change_default=True,)
    production_status = fields.Selection([('Pending', 'Pending'), ('Processing', 'Processing'),('Completed', 'Completed')],
             string='Processing status',  copy=False, index=True, change_default=True,)
    status = fields.Selection([
        ('Paco BWH', 'Paco BWH'), 
        ('MBN BWH', 'MBN BWH'),
        ('KTN BWH', 'KTN BWH'),
        ('3rd party', '3rd party'),
        ('Ned VN', 'Ned VN'),
        ('Local sale', 'Local sale'),
        ('Spot', 'Spot'),
        ('Unallocated', 'Unallocated'),
        ('Afloat', 'Afloat'),
        ('Factory', 'Factory'),
        ('Cancel', 'Cancel'),
        ('Allocated', 'Allocated'), 
        ('FOB', 'FOB'),
        ('Factory', 'Factory'),
        ('MBN', 'MBN'),
        ('Pending', 'Pending')], string='Ship by')

    p_ids = fields.Many2many('s.contract', compute='get_allocated_p', string='P-Contract')
    s_ids = fields.Many2many('s.contract', compute='get_allocated_s', string='S-Contract')
    allocation_ids = fields.One2many('sale.contract', 'shipping_id', 'Allocation')
    p_allocated_ids = fields.Char(string='P-Allocated', size=256, compute='get_allocated_p', store=True)
    date_sent = fields.Date(string="Date Sent")
    scertificate_id = fields.Many2one('ned.certificate', string='Certificate')
    spacking_id = fields.Many2one('ned.packing', string='Packing')
    certificate_id = fields.Many2one(related='shipping_ids.certificate_id',  string='Certificate', store = True)
    packing_id = fields.Many2one(related='shipping_ids.packing_id',  string='Packing')
    pss_sent = fields.Boolean(string="PSS Sent")
    pss_sent_date = fields.Date(string="PSS Sent Date")
    pss_approved = fields.Boolean(string="PSS Approved")
    pss_approved_date = fields.Date(string='PSS approved date')
    shipment_date = fields.Date(string="shipment Date", change_default=True)
    materialstatus = fields.Char(string="Material Status",size=256,change_default=True,)
    standard_id = fields.Many2one('product.product', string='Standard')
    fumigation_id = fields.Many2one('ned.fumigation', string='Fumigation')
    fumigation_date = fields.Date(string="Fumigation Date")
    shipped = fields.Boolean(string="Shipped" ,change_default =True)
    closing_time = fields.Datetime(string="Closing time")
    
    shipping_line_id = fields.Many2one('shipping.line', string='Shipping Line', copy=True, readonly=False)
    delivery_place_id = fields.Many2one('delivery.place', string='Delivery Place',
       domain="[('type', 'not in', ['purchase'])]")    
    pss_condition = fields.Selection([('pss', 'Pss'), ('none-pss', 'None PSS')], string='Pss Condition')
    bill_no = fields.Char(string="B/L no.")
    bill_date = fields.Date(string="ETD/ BL date")
    vessel = fields.Char(string="Vessel")
    voyage = fields.Char(string="Voyage")
    remarks = fields.Char(string="Important remarks")
    priority_by_month = fields.Char(string="Priority",change_default =True,)
    pss_send_schedule = fields.Date(string="1st PSS sent date")
    
    #Kiet
    si_received_date = fields.Date(string="SI received date")
    si_sent_date = fields.Date(string="SI sent date")
    nominated_etd = fields.Date(string="Nominated ETD")
    od_doc_rec_date = fields.Date(string="O.docs rec. date")
    od_doc_sent_date = fields.Date(string="O.docs Sent. date")
    awb_sent_no= fields.Char(string="AWB sent No.", size=256)
    
    #Duy them fields noi dong hang
    packing_place = fields.Selection([('factory','Factory-BMT'),
                                      ('sg','HCM'), # shortened from HCM
                                      ('bd','Binh Duong'),
                                      ('mn','Kho Molenberg Natie'),
                                      ('vn','Kho Vinacafe'),
                                      ('kn','Kho Katoen LT'),
                                      ('ka', 'Kho Katoen AP'),
                                      ('pa', 'Kho Pacorini')], string='Stuffing place')

    # Son them thong tin nhap tay cho ban in Invoice
    ross_weight = fields.Float(string="Ross Weight", digits=(12, 3))
    # net_weight = fields.Float(string="Net Weight", digits=(12, 3))
    description_of_goods = fields.Text(string="Description")
    other_detail = fields.Text(string="Other Detail")

    no_of_bag = fields.Float(string='No of bags')
    specs = fields.Char(size=256, string='Quality Detail')
    request_qty = fields.Float('Qty')
    origin  = fields.Selection([('VN', 'VN'), 
                               ('ID', 'ID'),
                               ('IN', 'IN'),
                               ('CO', 'CO'),
                               ('LA', 'LA'),
                               ('CI', 'CI'), # Ivory Coast
                               ('HN', 'HN'), # Honduras
                               ('BR', 'BR'), # Brazil
                               ('GU', 'GU'), # Guatemala
                               ('UG', 'UG') # Uganda
                               ], string='Origin') 
    shipt_month = fields.Many2one('s.period', string="Shipt month")
    pss_type = fields.Selection(related='contract_id.pss_type', selection=[('SAS','SAS'),('SAP','SAP'),('PSS','PSS'),('PSS+OTS','PSS+OTS'),('No','No')],string=" Pss type")
    start_of_ship_period = fields.Date(string="Start of Ship. period contract")
    end_of_ship_period = fields.Date(string="End of ship. Period contract")
    delivery_type= fields.Selection([('50','Shipment'),('10','Delivery')], string="Delivery type")
    end_of_ship_period_actual = fields.Date(related='contract_id.end_of_ship_period_actual', string="Del Period")
    pic_id = fields.Many2one('s.pic', string='PIC')

    precalculated_freight_cost = fields.Float(related='contract_id.precalculated_freight_cost', string="Freight")
    allocated_date = fields.Date(string='Allocation Date')
    eta = fields.Date(string='ETA')
    late_ship_end = fields.Date(string='Late Ship - BL vs End period')
    late_ship_est = fields.Date(string='Late Ship - BL vs nominated ETD')
    cause_by = fields.Text(string="Caused By")
    pss_sent_ids = fields.One2many(related='contract_id.pss_sent_ids', string='Pss')
    allocation_ids = fields.One2many('sale.contract', 'shipping_id', string='Allocations')
    
    allowed_franchise = fields.Float(related='contract_id.allowed_franchise', string="Franchise")
    
    
    certificated_ids = fields.Many2many('ned.certificate', 'certificate_shipping_instruction',
                                        'shipping_instruction_id', 'certificate_id', string='Certificate List')
    
    @api.onchange('shipping_ids','shipping_ids.product_qty')
    def check_qty_allocated(self):
        for this in self:
            si_list = self.search([('contract_id','=',this.contract_id.id)])
            for line in this.shipping_ids:
                qty_si = sum([x.product_qty for x in [y.shipping_ids.filtered(lambda r: r.product_id.id == line.product_id.id) for y in si_list]])
                qty_contract = sum([x.product_qty for x in this.contract_id.contract_line.filtered(lambda r: r.product_id.id == line.product_id.id)])
                if qty_si > qty_contract:
                    raise UserError(_('Quantity Contract have allocated.'))

    @api.onchange('shipment_date')
    def onchange_shipment_date(self):
        return
    ############err #########
        pss_mng_obj = self.env['pss.management']
        for this in self:
            pss_mng_id = pss_mng_obj.search([('shipping_id', '=', this.id)])
            if pss_mng_id:
                for idd in pss_mng_id:
                    pss_mng_id.write({'x_shipment_date': pss_mng_obj.browse(idd.id).shipping_id.shipment_date})
    
    # The function below loads information of sales contract against corresponding SI.
    def button_load_sc(self):
        if self.contract_id:
            if self.state == 'done' and not self.user_has_groups('sd_sale_contract.group_sale_contract_button'):
                raise UserError(_('Unable Load SI for contract %s.\n\t Please contact with your manager.') % (self.name))

            name = 'SI-' + self.contract_id.name
            val ={
                    'name':name,
                    'port_of_loading':self.contract_id.port_of_loading and self.contract_id.port_of_loading.id or False,
                    'port_of_discharge':self.contract_id.port_of_discharge and self.contract_id.port_of_discharge.id or False,
                    'shipment_date':self.contract_id.shipment_date or False,
                    'incoterms_id':self.contract_id.incoterms_id.id  or False,
                    'pss_condition': 'pss' if self.contract_id.pss == True else 'none-pss'
                    }
            self.write(val)
            
            self.partner_id = self.contract_id.partner_id.id
            
            self.shipping_ids.unlink()
            
            # self.env.cr.execute('''DELETE FROM shipping_instruction_line WHERE shipping_id = %s''' % (self.id))
            #Duy: list cac SI co chung contract_id
            si_list = self.search([('contract_id','=',self.contract_id.id),('id','!=', self.id)])
            qty_si = 0.0
            for contract in self.contract_id.contract_line:
                #Duy: kiem tra qty da chia cho cac SI trc do
                qty_si = sum([x.product_qty for x in [y.shipping_ids.filtered(lambda r: r.product_id.id == contract.product_id.id) for y in si_list]])
                if qty_si >= contract.product_qty:
                    raise UserError(_('Quantity Contract have allocated.'))
                else:
                    var = {
                        'certificate_id':contract.certificate_id.id,
                        'packing_id': contract.packing_id.id,
                        'name': contract.name or False, 'shipping_id': self.id or False, 'partner_id': self.partner_id.id or False,
                        'tax_id': [(6, 0, [x.id for x in contract.tax_id])] or False, 'company_id': self.company_id.id or False,
                        'price_unit': contract.price_unit or 0.0, 'product_id': contract.product_id.id or False, 
                        'product_qty': contract.product_qty - qty_si or 0.0,
                        'product_uom': contract.product_uom.id or False, 'state': 'draft', 
                        'certificate_id': contract.certificate_id.id or False,
                        'bags': contract.number_of_bags,
                        'gross_weight': contract.number_of_bags + contract.product_qty - qty_si}
                    self.env['shipping.instruction.line'].create(var)
            
            if self.contract_id.certificated_ids:
                self.certificated_ids = [(6, 0, [x.id for x in self.contract_id.certificated_ids])]
        return True
    
    
    
    #########################################################################################################
    shipment_date = fields.Date(string="shipment Date", change_default=True)
    
    # @api.model
    # def create(self, vals):
    #
    #     result = super(ShippingInstruction, self).create(vals)
    #     if not result.reference:
    #         result.reference = self.env['ir.sequence'].next_by_code('reference.shipping.instruction') or '/'
    #     return result

    def create_commercial_reference(self):
        for record in self:
            if not record.reference:
                record.reference = self.env['ir.sequence'].next_by_code('reference.shipping.instruction') or '/'
            else:
                raise UserError(_("Commercial Invoice Reference already exits."))
    
        
    @api.onchange('warehouse_id')
    def onchange_warehouse_id(self):
        if not self.warehouse_id:
            return {}
        values = {'shipment_from': self.warehouse_id.partner_id.id or False}
        self.update(values)
    
        
    def button_waiting(self):
        if not self.shipping_ids:
            raise UserError(_('You cannot approve a Shipping Instruction without any Shipping Instruction Line.'))
        self.write({'state': 'waiting','user_confirm': self.env.uid,'date_confirm': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
        
    def button_approve(self):
        if self.total_cont_qty != self.total_line_qty:
            raise UserError(_('Products qty have not packing out.'))
        self.write({'state': 'approved', 'user_approve': self.env.uid, 'date_approve': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
        
    def button_done(self):
        if not self.contract_ids:
            raise UserError(_('You cannot done a SI without any Sale Contract.'))
        self.write({'state': 'done'})
    
    def button_cancel(self):
        if self.state == 'done':
            raise UserError(_('Unable to cancel SI.'))
        
        if self.contract_ids:
            for line in self.contract_ids:
                if line.state == 'done':
                    raise UserError(_('Unable to cancel SI %s as some receptions have already been done.\n\t You must first cancel related NVS.') % (self.name))
                # if line.picking_ids:
                #     for i in line.picking_ids:
                #         if i.state == 'done':
                #             raise UserError(_('Unable to cancel SI %s as some receptions have already been done.\n\t You must first cancel related GDN.') % (self.name))
                if line.delivery_ids:
                    for j in line.delivery_ids:
                        if j.state == 'done':
                            raise UserError(_('Unable to cancel SI %s as some receptions have already been done.\n\t You must first cancel related DO.') % (self.name))
                            
            self.env.cr.execute('''DELETE FROM stock_move_line WHERE picking_id in 
                (SELECT sp.id FROM stock_picking sp join sale_contract sc on sc.id = sp.sale_contract_id WHERE sc.shipping_id = %(shipping_id)s);
            DELETE FROM stock_move WHERE picking_id in (SELECT sp.id FROM stock_picking sp join sale_contract sc on sc.id = sp.sale_contract_id WHERE sc.shipping_id = %(shipping_id)s);
            DELETE FROM stock_picking WHERE id in (SELECT sp.id FROM stock_picking sp join sale_contract sc on sc.id = sp.sale_contract_id WHERE sc.shipping_id = %(shipping_id)s);
            DELETE FROM delivery_order_line WHERE delivery_id in (SELECT de.id FROM delivery_order de join sale_contract sc on sc.id = de.contract_id WHERE sc.shipping_id = %(shipping_id)s);
            DELETE FROM delivery_order WHERE id in (SELECT de.id FROM delivery_order de join sale_contract sc on sc.id = de.contract_id WHERE sc.shipping_id = %(shipping_id)s);
            DELETE FROM sale_contract_line WHERE contract_id in (SELECT id FROM sale_contract WHERE shipping_id = %(shipping_id)s);
            DELETE FROM sale_contract WHERE id in (SELECT id FROM sale_contract WHERE shipping_id = %(shipping_id)s);''' % ({'shipping_id': self.id}))
        self.write({'state': 'cancel'})
    
    
    
    def create_nvs(self):
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('sd_sale_contract.action_view_wizard_nvs')
        form_view_id = imd.xmlid_to_res_id('sd_sale_contract.view_wizard_nvs')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[form_view_id, 'form']],
            'target': action.target,
            'res_model': action.res_model,
            }
        return result
    
    def action_view_contract_nvs(self):
        action = self.env.ref('sd_sale_contract.action_sale_contract_export')
        result = action.read()[0]
        contract_ids = sum([order.contract_ids.ids for order in self], [])
        if len(contract_ids) > 1:
            result['domain'] = "[('id','in',[" + ','.join(map(str, contract_ids)) + "]), ('state','!=','cancel')]"
        elif len(contract_ids) == 1:
            res = self.env.ref('sd_sale_contract.view_sale_contract_form', False)
            result['context'] = action.context
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = contract_ids and contract_ids[0] or False
        return result
    
        
    
    
    def action_view_invoices(self):
        for contract in self.contract_ids:
            for invoice in contract.invoice_ids:
                invoice_ids = (invoice.filtered(lambda r: r.state != 'cancel')) or False
                
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('account.action_invoice_tree1')
        list_view_id = imd.xmlid_to_res_id('account.invoice_tree')
        form_view_id = imd.xmlid_to_res_id('account.invoice_form')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'kanban'], [False, 'calendar'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        if len(invoice_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % invoice_ids.ids
        elif len(invoice_ids) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = invoice_ids.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result
    
class ShippingInstructionLine(models.Model):
    _name = "shipping.instruction.line"
    _inherit = ['mail.thread']
    _order = 'id desc'
    
    name = fields.Text(string='Description', required=True)
    shipping_id = fields.Many2one('shipping.instruction', string='Shipping Instruction')   
    sequence = fields.Integer(string='Sequence', default=10)
    company_id = fields.Many2one(related='shipping_id.company_id', string='Company', store=True, readonly=True)
    partner_id = fields.Many2one(related='shipping_id.partner_id', store=True, string='Customer')
    no_of_teus  = fields.Float(string='No. of teus')
    # #Eroo
    # state = fields.Selection([('draft', 'New'), ('approved', 'Approved'), ('cancel', 'Cancelled')],
    #       'shipping_id.state', string='Status', readonly=True, copy=False, store=True, default='draft')
    
    state = fields.Selection(related='shipping_id.state', string='Status', readonly=True, copy=False, store=True, default='draft')
    
    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)], change_default=True, required=True)
    product_qty = fields.Float(string='Qty', required=True, default=1.0,)
    product_uom = fields.Many2one('uom.uom', string='Uom', required=True)
    price_unit = fields.Float('Unit Price', required=True, default=0.0)
    tax_id = fields.Many2many('account.tax', string='Taxes')
    
    
    ############################################################
    shipping_no = fields.Char(related='shipping_id.name', string='SI No.')
    contract_no = fields.Many2one('s.contract',related='shipping_id.contract_id', string='Contract No.')
    si_date = fields.Date(related='shipping_id.date', string='SI Date.')
    partner_name = fields.Many2one(related='shipping_id.partner_id', string='Customer')
    shipment_date = fields.Date(related='shipping_id.shipment_date', string='Shipment Date.')
    
    
    bags = fields.Float(string='Bags')
    tare_weight = fields.Float(string='Tare Weight')
    gross_weight = fields.Float(string='Gross Weight')
    diff_net = fields.Float(string='Different Net Weight')
    
    
    def write(self, values):
        # for line in self:
        #     if values.get('product_qty') and line.shipping_id:
        #         msg = _("Qty : %.2f -> %.2f ") % (line.product_qty,values.get('product_qty'))
        #         line.shipping_id.message_post(body=msg)
        result = super(ShippingInstructionLine, self).write(values)
        return result
    
    ##########################################################################################
    
    # Ned contract ########################################################################
    @api.onchange('product_qty')
    def onchange_si_qty(self):
        si_list = self.env['shipping.instruction'].search([('contract_id','=',self.shipping_id.contract_id.id)])
        qty_si = sum([x.product_qty for x in [y.shipping_ids.filtered(lambda r: r.product_id.id == self.product_id.id) for y in si_list]])
        if self.product_qty and self.product_qty > qty_si:
            raise UserError(_('Quantity SI must be less than total Quantity Contract.'))
        
        
    packing_id = fields.Many2one('ned.packing', string='Packing')
    certificate_id = fields.Many2one('ned.certificate', string='Certificate')
    # Ned contract vn ########################################################################
    
    shipping_no = fields.Char(related='shipping_id.name', string='SI No.')
    si_date = fields.Date(related='shipping_id.date', string='SI Date.')
    partner_name = fields.Many2one(related='shipping_id.partner_id', string='Customer')
    shipment_date = fields.Date(related='shipping_id.shipment_date', string='Shipment Date.')
    
    
    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return {'domain': {'product_uom': []}}

        vals = {}
        domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        if not (self.product_uom and (self.product_id.uom_id.category_id.id == self.product_uom.category_id.id)):
            vals['product_uom'] = self.product_id.uom_id

        product = self.product_id.with_context(
            lang=self.contract_id.partner_id.lang,
            partner=self.contract_id.partner_id.id,
            quantity=self.product_qty,
            uom=self.product_uom.id
        )

        name = product.name_get()[0][1]
        if product.description_sale:
            name += '\n' + product.description_sale
        vals['name'] = name

        self._compute_tax_id()

        if self.contract_id.partner_id:
            vals['price_unit'] = self.env['account.tax']._fix_tax_included_price(product.price, product.taxes_id, self.tax_id)
        self.update(vals)
        return {'domain': domain}
        
class BesContainers(models.Model):
    _name = "bes.containers"
    _inherit = ['mail.thread']
    _order = 'id asc'
    
    @api.model
    def _default_uom_id(self):
        uom_ids = self.env['uom.uom'].search([('name', '=', 'kg')], limit=1)
        return uom_ids
    
    name = fields.Char(string="No Of Containers", required = True)
    seal_no = fields.Char(string='Seal No.', copy=False, index=True)
    shipping_id = fields.Many2one('shipping.instruction', string='No Of Containers', ondelete='cascade', index=True, copy=False)
    product_qty = fields.Float('Qty', default=1)
    product_uom = fields.Many2one('uom.uom', 'UoM', default=_default_uom_id)
    

    
    
    
