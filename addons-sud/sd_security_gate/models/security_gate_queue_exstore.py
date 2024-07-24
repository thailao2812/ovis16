# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
from lxml import etree

class NedSecurityGateQueue(models.Model):
    _inherit = "ned.security.gate.queue"
    

    @api.onchange('shipping_id')
    def onchange_si_id(self):
        if self.shipping_id:
        	for line in self.shipping_id.shipping_ids:
	            # shipping_info = self.env['shipping.instruction'].browse(self.shipping_id.id)
	            return {'value': {'product_id': line.product_id.id,
	            				  'packing_id': line.packing_id.id,
                                  'customer_id': self.shipping_id.partner_id.id,
                                  'supplier_id': self.shipping_id.partner_id.id,
	            				  }
            			}
	        return {'value': {}}

    customer_id = fields.Many2one('res.partner', string='Customer')
    trucking_id = fields.Many2one('res.partner', string='Trucking Co', states={'approved': [('readonly', True)],'closed': [('readonly', True)]})
    first_cont = fields.Char(string='First Container') 
    last_cont = fields.Char(string='Last Container')
    shipping_id = fields.Many2one('shipping.instruction', string='SI No.', ondelete='cascade', readonly=True, required=False, states={'draft': [('readonly', False)],'sec_confirm': [('readonly', False)]})
    product_id = fields.Many2one('product.product', string='Product')
    packing_id = fields.Many2one('ned.packing', string='Packing Type')
    issue_state = fields.Selection(related='picking_ids.state', string='Issue State', store = False)
    nvs_nls_id = fields.Many2many('sale.contract', 'security_gate_sale_contract_rel', 'security_gate_id', 'contract_id', string='Sale Contract', 
                            readonly=True, states={'draft': [('readonly', False)],'sec_confirm': [('readonly', False)]})
    delivery_id = fields.Many2many('delivery.order', 'security_gate_delivery_order_rel', 'security_gate_id', 'delivery_id',string="Do no.", 
                            readonly=True, states={'draft': [('readonly', False)],'sec_confirm': [('readonly', False)]})
    delivery_ids = fields.One2many('delivery.order','security_gate_id',string = 'Deliverys')
    post_shipment_ids = fields.One2many('post.shipment','security_gate_id',string = 'Post Shipment')
    first_weight = fields.Float(string='First Weight (kg)', readonly=True, digits=(12, 0))
    second_weight = fields.Float(string='Second Weight (kg)', readonly=True, digits=(12, 0))
    tare_weight = fields.Float(string='Tare Weight (kg)', readonly=True, digits=(12, 2))
    net_weight = fields.Float(string='Net Weight (kg)', readonly=True, digits=(12, 0))


    def button_logistics_confirm(self):
        for this in self:
            this.state = 'logistics_confirm'
            this.product_ids = this.product_id

    def button_sec_confirm(self):
        for this in self:
            sql ='''
            SELECT COUNT(id) as total
            FROM ned_security_gate_queue 
            WHERE date(timezone('UTC',arrivial_time::timestamp)) = date(timezone('UTC','%s'::timestamp))
                    AND type_transfer = '%s' AND state='sec_confirm'
            '''%(datetime.now(),self.env.context.get('default_type_transfer'))
            self._cr.execute(sql)
            result_sql = self._cr.dictfetchall()
            # print(result_sql, self.env.context.get('default_type_transfer'))
            total_qty_all = result_sql and result_sql[0] and result_sql[0]['total'] or 0

            this.parking_order = total_qty_all + 1
            this.arrivial_time = datetime.now()
            this.state = 'sec_confirm'

    def button_load_do_ps(self):
        for this in self:
            do_list=[]
            for item in this.nvs_nls_id:
                do_item = self.env['delivery.order'].sudo().search([('contract_id','=',item.id),('trucking_no','=',this.license_plate)])
                if not do_item:
                    raise UserError(_('DO find not found. Please check Vehicle/DO No.'))
                else:
                    do_list.append(do_item.id)
                    do_item.update({'security_gate_id': this.id,
                                    'trucking_id': this.trucking_id})
                    do_item.picking_id.update({'security_gate_id': this.id,
                                    'trucking_id': this.trucking_id})

            for _do in do_list:
                ps_item = self.env['post.shipment'].sudo().search([('do_id','=',_do)],limit =1)
                if not ps_item:
                    ps_obj = ps_item.create({'name':'New'})
                    ps_obj.do_id = _do
                    ps_obj.button_load()
                    self.create_postshipment_line(ps_obj.id)
                else:
                    ps_item.update({'security_gate_id': this.id, 'truck_plate': this.license_plate})
                    self.create_postshipment_line(ps_item.id)

            this.delivery_id = do_list


    def button_create_do_ps(self):
        for this in self:
            do_list=[]
            for item in this.nvs_nls_id:
                do_item = self.env['delivery.order'].sudo().search([('security_gate_id','=',this.id),('contract_id','=',item.id)],limit =1)
                if not do_item:
                    # vals['name'] = self.env['ir.sequence'].next_by_code('delivery.order')
                    do_obj = do_item.create({'type': 'Sale',
                                            'security_gate_id': this.id,})
                    do_obj.contract_id=item.id
                    do_obj.button_load_do()
                    do_obj.trucking_id = this.trucking_id
                    do_obj.trucking_no = this.license_plate
                    do_list.append(do_obj.id)
                else:
                    do_item.contract_id=item.id
                    do_item.button_load_do()
                    do_item.trucking_id = this.trucking_id
                    do_item.trucking_no = this.license_plate
                    do_list.append(do_item.id)

            for _do in do_list:
                ps_item = self.env['post.shipment'].sudo().search([('do_id','=',_do)],limit =1)
                if not ps_item:
                    ps_obj = ps_item.create({'name':'New'})
                    ps_obj.do_id = _do
                    ps_obj.button_load()
                    self.create_postshipment_line(ps_obj.id)
                else:
                    ps_item.update({'security_gate_id': this.id, 'truck_plate': this.license_plate})
                    self.create_postshipment_line(ps_item.id)

            this.delivery_id = do_list


    def create_postshipment_line(self, post_id):
        cont_no = [self.first_cont, self.last_cont]
        if not cont_no == []:
            for _cont in cont_no:
                psl_item = self.env['post.shipment.line'].sudo().search([('cont_no','=',_cont)])
                if not psl_item:
                    ps_line = {
                        'cont_no': _cont,
                        'loading_date': datetime.now(),
                        'post_id': post_id,
                    }
                    self.env['post.shipment.line'].sudo().create(ps_line)
                else:
                    psl_item.update({'loading_date': datetime.now()})
        return True




