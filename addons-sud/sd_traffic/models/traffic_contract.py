# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError
myear = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
lst_status = ['Paco BWH', 'MBN BWH', 'KTN BWH', '3rd party', 'Ned VN', 'Local sale', 'Spot', 'Unallocated', 'Afloat', 'Factory', 'Cancel']


        
    
class ResPartner(models.Model):
    _inherit = 'res.partner'

    def name_get(self):
        result = []
        for pro in self:
            if self._context.get('partner_traffic', False) == True:
                result.append((pro.id, pro.name))
            else:
                if pro.partner_code:
                    code = '['+ pro.partner_code +'] ' + pro.name 
                    result.append((pro.id, pro.name))
                else:
                    result.append((pro.id, pro.name))
        
        return result

class TrafficContract(models.Model):
    _inherit = 'traffic.contract'

    # Use this file py for traffic contract
    shipby_id = fields.Many2one('s.ship.by', string='Shipped By')
    status = fields.Selection([('Paco BWH', 'Paco BWH'),
                               ('MBN BWH', 'MBN BWH'),
                               ('KTN BWH', 'KTN BWH'),
                               ('3rd party', '3rd party'),
                               ('Ned VN', 'Ned VN'),
                               ('Local sale', 'Local sale'),
                               ('Spot', 'Spot'),
                               ('Unallocated', 'Unallocated'),
                               ('Afloat', 'Afloat'),
                               ('Factory', 'Factory'),
                               ('Cancel', 'Cancel'), ], string='Shipped By.')
    allocated_date = fields.Date(string='Allocation Date')
    shipt_month = fields.Many2one('s.period', string="Shipt month")
    origin = fields.Selection([('VN', 'VN'),
                               ('ID', 'ID'),
                               ('IN', 'IN'),
                               ('CO', 'CO'),
                               ('LA', 'LA'),
                               ('CI', 'CI'),  # Ivory Coast
                               ('HN', 'HN'),  # Honduras
                               ('BR', 'BR'),  # Brazil
                               ('GU', 'GU'),  # Guatemala
                               ('UG', 'UG'),  # Uganda
                               ('PE', 'PE')  # Peru
                               ], string='Origin')  # Guatemala  # Guatemala
    origin_new = fields.Many2one('res.country', string="Origin")
    name = fields.Char(string='S Contract')
    client_ref = fields.Char(string="Client ref.")
    partner_id = fields.Many2one('res.partner', string='Customer')
    p_qty = fields.Float(string="Ctr. Q'ty (Kg)")
    no_of_pack = fields.Float(string='No. of bag')
    standard_id = fields.Many2one('product.product', string='Standard')
    certificate_id = fields.Many2one('ned.certificate', string='Certificate')
    p_quality = fields.Text(string='Quality')
    packing_id = fields.Many2one('ned.packing', string='Packing')
    pss_type = fields.Selection(
        selection=[('SAS', 'SAS'), ('SAN', 'SAN'), ('SAP', 'SAP'), ('PAP', 'PAP'), ('PSS', 'PSS'), ('SOD', 'SOD'),
                   ('PSS+OTS', 'PSS+OTS'), ('No', 'No')], string=" Pss type")
    incoterms_id = fields.Many2one('account.incoterms', string='Term')
    start_of_ship_period = fields.Date(string="Start of Ship. period contract")
    end_of_ship_period = fields.Date(string="End of ship. Period contract")
    delivery_type = fields.Selection([('50', 'Shipment'), ('10', 'Delivery')], string="Delivery type")
    end_of_ship_period_actual = fields.Date(string="Delivery Period")
    pic_id = fields.Many2one('s.pic', string='PIC')
    port_of_loading = fields.Many2one('delivery.place', string='POL')
    port_of_discharge = fields.Many2one('delivery.place', string='POD')
    precalculated_freight_cost = fields.Float(string="Precalculated freight Cost")
    p_contract_link = fields.Many2many('s.contract', 'traffic_contract_pcontract_rel', 'sid', 'pid',
                                       string='P-Allocated')
    x_p_contract_link = fields.Char(string='P-Allocated')
    # p_allocated_link = fields.Char(string='P-Allocated', size=256)
    shipper_id = fields.Char(string='Shipper', size=256)
    si_sent_date = fields.Date(string="SI sent date")
    si_received_date = fields.Date(string="SI received date")
    pss_send_schedule = fields.Date(string='1st PSS Send Date', compute='_compute_pss_send_schedule', store=True)
    pss_amount_send = fields.Char(string='Amount of PSS sent', size=256, compute='_compute_pss_send_schedule', store=True)
    pss_approved_date = fields.Date(string='PSS approved date')
    freight = fields.Float(string="freight")
    shipping_line_id = fields.Many2one('shipping.line', string='Shipping Line')
    factory_etd = fields.Date(string='Stuffing Date')
    nominated_etd = fields.Date(string="Nominated ETD")
    bill_date = fields.Date(string="ETD/ BL date")
    booking_ref_no = fields.Char(string='Booking No./ BL No.')
    pss_sent_date = fields.Date(String="PSS Sent Date")
    eta = fields.Date(string='ETA')
    late_ship_end = fields.Date(string='Late Ship - BL vs End period')
    late_ship_est = fields.Date(string='Late Ship - BL vs nominated ETD')
    cause_by = fields.Text(string="Caused By")
    remarks = fields.Char(string="Important remarks")
    pss_late_ontime = fields.Char(string='Quality Detail', size=128)
    act_freight_cost = fields.Float(string='Actual Freight Cost')
    od_doc_rec_date = fields.Date(string="O.docs rec. date")
    od_doc_rec_awb = fields.Char(string="O.docs rec. AWB No.", size=256)
    od_doc_sent_date = fields.Date(string="O.docs Sent. date")
    awb_sent_no = fields.Char(string="AWB sent No.", size=256)
    x_remark1 = fields.Char(string="Remark 1", size=256)
    x_remark2 = fields.Char(string="Remark 2", size=256)
    state = fields.Selection([('draft', 'Draft'), ('linked', 'Linked')], string='Status')
    pss_sent_ids = fields.One2many('pss.sent', 't_contract_id', string='Pss')
    parent_id = fields.Many2one('traffic.contract', string='Parent')
    x_stuff_date = fields.Date(string='Stuffing Date To')
    x_stuff_place = fields.Char(string='Stuffing Place', size=256)
    shipment_status = fields.Char('Shipment Status', size=128)
    contract_mship = fields.Many2one('s.period', 'Contractual Shipment Month')
    counter_pt = fields.Char('Counter Party', size=256)
    ps = fields.Char('PS', size=256, default='S')

    @api.constrains('name')
    def _check_constrains_name(self):
        for record in self:
            check_name = self.search([
                ('name', '=', record.name),
                ('id', '!=', record.id)
            ], limit=1)
            if check_name:
                raise UserError(_("You cannot create duplicate name for S Contract!"))

    @api.depends('pss_sent_ids', 'pss_sent_ids.date_sent')
    def _compute_pss_send_schedule(self):
        for record in self:
            if record.pss_sent_ids:
                record.pss_amount_send = len(record.pss_sent_ids)
                record.pss_send_schedule = record.pss_sent_ids[0].date_sent or False
            else:
                record.pss_amount_send = 0
                record.pss_send_schedule = False


    def open_form_view(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _("Traffic Contract"),
            'res_model': 'traffic.contract',
            'view_mode': 'form',
            'domain': [('id', 'in', self.ids)],
            'res_id': self.id,
            'views': [(self.env.ref('sd_traffic.view_traffic_contract_form').id, 'form')],
        }

