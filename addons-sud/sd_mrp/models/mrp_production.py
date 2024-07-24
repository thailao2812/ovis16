# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

from datetime import datetime
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"    

class MrpProduction(models.Model):
    _inherit = 'mrp.production'
    
    def get_material_request(self):
        for rc in self:
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 's.import.file',
                'view_id': self.env.ref('sd_mrp.view_mrequest_import_file_form').id,
                'target': 'new',
                'context': {'default_mrp_id': rc.id}
            }
    
    @api.onchange("warehouse_id")
    def onchange_warehouse(self):
        if self.warehouse_id:
            picking_type_obj = self.env['stock.picking.type'].search([('warehouse_id','=',self.warehouse_id.id),('code','=','production_in')])
            self.picking_type_id = picking_type_obj and picking_type_obj.id or False
        # else:
        #     if self.picking_type_id:
        #     self.picking_type_id = False
    
    @api.onchange("bom_id")
    def onchange_bom(self):
        if self.bom_id:
            self.notes = self.bom_id.detail or ''
    
    def action_to_draft(self):
        if len(self.move_line_finished_good_ids) ==0 and len(self.move_line_material_ids) ==0:
            self.state = 'draft'
        else:
            raise UserError(_('This Manufacturing Order have had GIP or GRP already. You can not set to draft!!!'))

    def action_cancel(self):
        """ Kiểm tra các điều kiện rùi cập nhật trạng thái cancel """
        if self.state == 'done':
            raise UserError(_('The Other is Done, cannot cancel'))
        # Trường hợp đã tạo git rùi thì ko có tạo phiếu Cancel
        if self.request_count > 0:
            raise UserError(_('You have Request Material for this MO, cannot Cancel it!'))

        self.state = 'cancel'
        # self._action_cancel()
        return True
    
    def action_confirm(self):
        for production in self:
            production.state = 'confirmed'
        return True
    
    @api.depends('company_id')
    def _compute_picking_type_id(self):
        domain = [
            ('code', '=', 'production_in'),
            ('warehouse_id.company_id', 'in', self.company_id.ids),
        ]
        picking_types = self.env['stock.picking.type'].search_read(domain, ['company_id'], load=False, limit=1)
        picking_type_by_company = {pt['company_id']: pt['id'] for pt in picking_types}
        for mo in self:
            if mo.picking_type_id and mo.picking_type_id.company_id == mo.company_id:
                continue
            mo.picking_type_id = picking_type_by_company.get(mo.company_id.id, False)
        return
    
    
    @api.model
    def _domain_picking_type(self):
        ids =  "[('id', 'in', %s)]" % self.env.user._picking_type_domain()
        return ids
    
        
    picking_type_id = fields.Many2one(
        'stock.picking.type', 'Operation Type', copy=True, readonly=False,
        compute='_compute_picking_type_id', store=True, 
        #domain="[('code', '=', 'production_in'), ('company_id', '=', company_id)]",
        domain=lambda self: self._domain_picking_type(),
        required=False, check_company=True, index=True)
    
    @api.depends('product_id', 'company_id')
    def _compute_production_location(self):
        for production in self:
            if production.warehouse_id:
                production.production_location_id = production.warehouse_id.lot_stock_id.id
    
    production_location_id = fields.Many2one('stock.location', "Production Location", compute="_compute_production_location", store=True)
    
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('progress', 'In Progress'),
        ('to_close', 'To Close'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')], string='State', copy=False, index=True, readonly=True,  default="draft", compute=False,
        help=" * Draft: The MO is not confirmed yet.\n"
             " * Confirmed: The MO is confirmed, the stock rules and the reordering of the components are trigerred.\n"
             " * In Progress: The production has started (on the MO or on the WO).\n"
             " * To Close: The production is done, the MO has to be closed.\n"
             " * Done: The MO is closed, the stock moves are posted. \n"
             " * Cancelled: The MO has been cancelled, can't be confirmed anymore.")
    
    #

    @api.model_create_multi
    def create(self, vals_list):
        
        new_id = super().create(vals_list)
        if new_id.bom_id and new_id.bom_id.code:
            new_id.name = new_id.bom_id.code + self.env['ir.sequence'].next_by_code('mrp.production')
        return new_id

    def _default_warehouse(self):
        warehouse_ids = self.env['stock.warehouse'].with_context(user_workers=True).search(
            [('company_id', '=', self.env.user.company_id.id)])
        # default with user only working 1 company account analytic
        if warehouse_ids:
            id = warehouse_ids[0]
            return id
        else:
            return False
    
    def _default_warehouse(self):
        warehouse_ids = self.env['stock.warehouse'].with_context(user_workers=True).search(
            [('company_id', '=', self.env.user.company_id.id)])
        # default with user only working 1 company account analytic
        if warehouse_ids:
            return warehouse_ids[0]
    
    @api.model
    def _domain_warehouse(self):
        return "[('id', 'in', %s)]" % self.env.user._warehouses_domain()
    
    warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse", default=_default_warehouse, related='', store = True, 
                        domain=lambda self: self._domain_warehouse())
    
    grade_id = fields.Many2one('product.category', string='Group by Grade', related='bom_id.grade_id', store=True)
    date_finished = fields.Datetime( string="Date Finished")
    
    move_line_finished_good_ids = fields.One2many('stock.move.line', 'finished_id',string="Finished product", )
            #domain=[('state', '=', 'done'), ('picking_id.picking_type_id.code', '=', 'production_in'),('location_dest_id.usage', '=', 'internal')],)
    move_line_material_ids = fields.One2many('stock.move.line', 'material_id',string="Material product")
    batch_type = fields.Char(related='bom_id.type_code',string ='Type',readonly =True,store =True)
    
    direct_labour_ids = fields.One2many('direct.labour', 'production_id',string="Direct labour")
    
    @api.depends('product_uom_id', 'product_qty', 'product_id.uom_id')
    def _compute_product_uom_qty(self):
        for production in self:
            if production.product_id and production.product_id.uom_id != production.product_uom_id:
                production.product_uom_qty = production.product_uom_id._compute_quantity(production.product_qty, production.product_id.uom_id)
            else:
                production.product_uom_qty = production.product_qty
    
    def create_report_pnl(self):
        for production in self:
            bactch_report_ids = self.env['batch.report'].sudo().search([('production_id','=', production.id)])
            if bactch_report_ids:
                bactch_report_ids.load_data()
            else:
                bactch = self.env['batch.report'].sudo().create({'production_id':production.id})
                bactch.load_data()
        # ##########################################################################################################################################################################
            type ='normal'
            if production.name[0:3] != 'BTA':
                type = 'upgrade'
            analysis_ids = self.env['production.analysis'].sudo().search([('production_id','=',production.id)])
            if analysis_ids:
                if analysis_ids.type =='normal':
                    analysis_ids.load_data()
                else:
                    analysis_ids.load_data_upgrade()
            else:
                analysis = self.env['production.analysis'].sudo().create({'production_id':production.id,'type':type})
                if type =='normal':
                    analysis.load_data()
                else:
                    analysis.load_data_upgrade()
                # if this.company_id.res_user_ids:
                #     self.send_mail(analysis)
                    
                    
    def button_mark_done(self):
        #Kiet hàm check lại thông tin 
        for production in self:
            note = ''
            if len(production.move_line_material_ids.filtered(lambda d:d.state not in('cancel','done'))) >= 1:
                for gip in production.move_line_material_ids.filtered(lambda d:d.state not in('cancel','done')):
                    note += gip.picking_id.name +'; ' 
                raise UserError(_('Please done GIP: \n %s \n before done this Manufacturing Order - %s')%(note, production.name))

            if len(production.move_line_finished_good_ids.filtered(lambda d:d.state not in('cancel','done'))) >= 1:
                for grp in production.move_line_finished_good_ids.filtered(lambda d:d.state not in('cancel','done')):
                    note += grp.picking_id.name +';' 
                raise UserError(_('Please done GRP: \n %s \n before done this Manufacturing Order - %s')%(note, production.name))
             
            if production.product_issued ==0 and production.product_received ==0:
                raise UserError(_('The total Issued amount and total received amount = 0. You can not Done this MO - %s , please check again!!')%(production.name))
             
            if production.product_balance > 0:
                raise UserError(_('The balance amount of this MO - %s,  > 0. You can not Done this MO!!')%(production.name))
            
            production.write({
                'date_finished': fields.Datetime.now(),
                # Kiệt doạn này cần sửa lại thành phẩm sản xuất được
                #'product_qty': production.qty_produced,
                'priority': '0',
                'is_locked': True,
                'state': 'done',
            })
        self._compute_qty()
        self.create_report_pnl()
        
            
                    
    
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
                    # genermaterate templates for followers and not followers
                    fol_values = template_fol.generate_email(new_message.id, fields=['body_html', 'subject'])
                    # send email
                    new_emails, new_recipients_nbr = partner._notify_send(fol_values['body'], fol_values['subject'], recipient_template_values['followers'], **base_mail_values)
                    emails |= new_emails
                emails.send()
            except:
                pass

        
    def fix_compute_qty(self):
        self._compute_qty()
        
    @api.depends('state','move_line_material_ids','move_line_material_ids.picking_id.state','move_line_finished_good_ids','move_line_finished_good_ids.picking_id.state')
    def _compute_qty(self):
        for production in self:
            product_issued = 0.0
            product_basis_issued =0.0
            product_received =0.0
            product_received_loss =0.0   #SON thêm field loss tách riêng ra total Output qty
            product_loss_percent = 0.000
            stored_loss_in =0.0
            stored_loss_out =0.0
            
            #erro Kiet
            for consumed in production.move_line_material_ids:
                if consumed.state !='done':
                    continue
                product_issued += consumed.init_qty or 0.0 # -> quy chuan ve 1 trong luong duy nhat init_qty (yc ngay: 10/07/2019)
                product_basis_issued += consumed.qty_done or 0.0
                stored_loss_in += consumed.init_qty or 0.0 
                
            for produced in production.move_line_finished_good_ids:
                if produced.state !='done':
                    continue
                
                if produced.product_id.default_code =='PROCESSING LOSS':
                    product_received_loss += produced.init_qty or 0.0 # -> quy chuan ve 1 trong luong duy nhat chuyen doi tu weighbridge init_qty (yc ngay: 10/07/2019)
                else:
                    # SON: Lấy giá trị cho Output từ weightbridge (cân lại) thay vì từ init (net) -> quy chuan ve 1 trong luong duy nhat chuyen doi tu weighbridge init_qty (yc ngay: 10/07/2019)
                    product_received += produced.init_qty or 0.0
                    stored_loss_out += produced.init_qty or 0.0
            
            production.product_basis_issued  = product_basis_issued
            production.product_issued = product_issued
            production.product_received = product_received
            production.product_balance = product_issued - (product_received + product_received_loss)
            production.product_received_loss = product_received_loss
            if product_issued != 0:
                product_loss_percent = (product_received_loss / product_issued) * 100
            production.product_loss_percent = product_loss_percent
            
            # for df in production.move_lines:
            #     if df.picking_type_code =='phys_adj':
            #         stored_loss += df.init_qty or 0.0
            if production.product_issued != 0:
                if production.state == 'done':
                    production.stored_loss = (stored_loss_in - stored_loss_out) != 0 and (stored_loss_in - stored_loss_out) / stored_loss_in * 100 or 0.0
            
    product_issued = fields.Float(compute='_compute_qty', string='Issue', store= True, digits=(12, 0))
    product_basis_issued = fields.Float(compute='_compute_qty',store= True, string='Basis Issue', digits=(12, 0))
    product_received = fields.Float(compute='_compute_qty', store= True, string='Received', digits=(12, 0))
    product_balance = fields.Float(compute='_compute_qty', store= True, string='Balance',digits=(12, 0))
    #SON thêm field loss tách riêng ra total Output qty
    product_received_loss = fields.Float(compute='_compute_qty', store= True, string='Loss Received', digits=(12, 0))
    product_loss_percent = fields.Float(compute='_compute_qty', string='%_Loss', digits=(12, 2), store= True)
    stored_loss = fields.Float(compute='_compute_qty', string='% Processing Loss', store= True, digits=(12, 2))
    
    
    product_id = fields.Many2one(
        'product.product', string= 'Product', store=True, copy=False, readonly=True, required=False, compute=False,
        states={'draft': [('readonly', False)]})
    
    bom_id = fields.Many2one('mrp.bom', string='Bill of Material',store=True, readonly=True, compute=False,
                             domain="""[(1, '=', 1)]""", required=True,
                             states={'draft': [('readonly', False)]},
    help="Bill of Materials allow you to define the list of required components to make a finished product.")
    
    notes = fields.Text(string="Notes")
    
    product_uom_id = fields.Many2one(
        'uom.uom', string='Product Unit of Measure',  
        readonly=False, required=False, store=True, copy=False)
    
    @api.depends('request_ids')
    def _compute_requests(self):
        for mrp in self:
            mrp.request_count = len(mrp.request_ids)
    
    request_count = fields.Integer(compute='_compute_requests', string='Receptions', default=0)
    request_ids = fields.One2many('request.materials', 'production_id', string='Request Materials', copy=False)
    
    def action_view_request(self):
        request_ids = self.mapped('request_ids')
        result = {
            
            "type": "ir.actions.act_window",
            "res_model": "request.materials",
            "domain": [('id', 'in', request_ids.ids)],
            "context": {"create": False},
            "name": "Request Materials",
            'view_mode': 'tree,form',
            }
            
        return result
    
        
    

