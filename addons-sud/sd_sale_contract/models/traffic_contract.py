# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

myear = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
lst_status = ['Paco BWH', 'MBN BWH', 'KTN BWH', '3rd party', 'Ned VN', 'Local sale', 'Spot', 'Unallocated', 'Afloat', 'Factory', 'Cancel']
    
    
class TrafficContract(models.Model):
    _name = "traffic.contract"
    _order = 'write_date desc'
                    
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
                               ('Cancel', 'Cancel'),], string='Shipped By.')
    allocated_date = fields.Date(string='Allocation Date')
    shipt_month = fields.Many2one('s.period', string="Shipt month")
    origin  = fields.Selection([('VN', 'VN'), 
                               ('ID', 'ID'),
                               ('IN', 'IN'),
                               ('CO', 'CO'),
                               ('LA', 'LA'),
                               ('CI', 'CI'), # Ivory Coast
                               ('HN', 'HN'), # Honduras
                               ('BR', 'BR'), # Brazil
                               ('GU', 'GU'),
                               ('UG', 'UG') # Uganda
                               ], string='Origin') # Guatemala
    name = fields.Char(string='S Contract', size=128)
    client_ref = fields.Char(string="Client ref.", size=128)
    partner_id = fields.Many2one('res.partner', string='Customer')
    p_qty = fields.Float(string="Ctr. Q'ty (Kg)")
    no_of_pack = fields.Float(string='No. of bag')
    standard_id = fields.Many2one('product.product', string='Standard')
    certificate_id = fields.Many2one('ned.certificate', string='Certificate')
    p_quality = fields.Text(string='Quality')
    packing_id = fields.Many2one('ned.packing', string='Packing')
    pss_type = fields.Selection(selection=[('SAS','SAS'),('SAN','SAN'),('SAP','SAP'),('PAP','PAP'),('PSS','PSS'),('PSS+OTS','PSS+OTS'),('No','No')], string=" Pss type")
    incoterms_id = fields.Many2one('account.incoterms', string='Term')
    start_of_ship_period = fields.Date(string="Start of Ship. period contract")
    end_of_ship_period = fields.Date(string="End of ship. Period contract")
    delivery_type= fields.Selection([('50','Shipment'), ('10','Delivery')], string="Delivery type")
    end_of_ship_period_actual = fields.Date(string="Delivery Period")
    pic_id = fields.Many2one('s.pic', string='PIC')
    port_of_loading = fields.Many2one('delivery.place', string='POL')
    port_of_discharge = fields.Many2one('delivery.place', string='POD')
    precalculated_freight_cost = fields.Float(string="Precalculated freight Cost")
    p_contract_link = fields.Many2many('s.contract', 'traffic_contract_pcontract_rel', 'sid', 'pid', string='P-Allocated')
    x_p_contract_link = fields.Char(string='P-Allocated', size=256)
    # p_allocated_link = fields.Char(string='P-Allocated', size=256)
    shipper_id = fields.Char(string='Shipper', size=256)
    si_sent_date = fields.Date(string="SI sent date")
    si_received_date = fields.Date(string="SI received date")
    pss_send_schedule = fields.Date(string = '1st PSS Send Date')
    pss_amount_send = fields.Char(string='Amount of PSS sent', size=256)
    pss_approved_date = fields.Date(string='PSS approved date')
    freight = fields.Float(string="freight")
    shipping_line_id = fields.Many2one('shipping.line', string='Shipping Line')
    factory_etd = fields.Date(string = 'Stuffing Date')
    nominated_etd = fields.Date(string="Nominated ETD")
    bill_date = fields.Date(string="ETD/ BL date")
    booking_ref_no = fields.Char(string='Booking No./ BL No.')
    pss_sent_date = fields.Date(string="PSS Sent Date")
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

    def split_scontract(self):
        new_record = 0
        for record in self:
            return {
                'name': 'Split Shipment',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'shipping.split',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': {'default_traffic_id': record.id},
            }

    def sync_scontract(self):
        s_contract_obj = self.env['s.contract']
        s_contractl_obj =  self.env['s.contract.line']
        # ids = self.env['traffic.contract'].search(['|', ('state', '!=', 'linked'), ('state', '=', False)])
        # for idd in ids:
        for idd in self:
            record = self.browse(idd.id)
            # try:
            vals = {
                # 'shipby_id ': record.shipby_id and record.shipby_id.id or 0,
                'status': record.status or '',
                'shipt_month': record.shipt_month and record.shipt_month.id or 0,
                'origin': record.origin and record.origin or '',
                'name': record.name and record.name + '-B' or '',
                'client_ref': record.client_ref and record.client_ref or '',
                'partner_id': record.partner_id and record.partner_id.id or 0,
                'p_qty': record.p_qty and record.p_qty or 0,
                'no_of_pack': record.no_of_pack and record.no_of_pack or 0,
                'standard_id': record.standard_id and record.standard_id.id or 0,
                'certificate_id': record.certificate_id and record.certificate_id.id or 0,
                'p_quality': record.p_quality and record.p_quality or '',
                'packing_id': record.packing_id and record.packing_id.id or 0,
                'pss_type': record.pss_type and record.pss_type or '',
                'incoterms_id': record.incoterms_id and record.incoterms_id.id or 0,
                'delivery_type': record.delivery_type or '',
                'pic_id': record.pic_id and record.pic_id.id or 0,
                'port_of_loading': record.port_of_loading and record.port_of_loading.id or 0,
                'port_of_discharge': record.port_of_discharge and record.port_of_discharge.id or 0,
                'precalculated_freight_cost': record.precalculated_freight_cost or 0,
                'shipper_id': record.shipper_id and record.shipper_id or 0,
                'pss_amount_send': record.pss_amount_send and record.pss_amount_send or 0,
                'freight': record.freight or 0,
                'shipping_line_id': record.shipping_line_id and record.shipping_line_id.id or 0,
                'booking_ref_no': record.booking_ref_no or '',
                'cause_by': record.cause_by or '',
                'remarks': record.remarks or '',
                'act_freight_cost': record.act_freight_cost or 0,
                'awb_sent_no': record.awb_sent_no or '',
                'type': 'export',
                'traffic_link_id': record.id,
                'od_doc_rec_awb': record.od_doc_rec_awb or ''
            }
            if record.allocated_date:
                vals.update({
                    'allocated_date': record.allocated_date and record.allocated_date or '',
                })
            if record.start_of_ship_period:
                vals.update({
                    'start_of_ship_period': record.start_of_ship_period and record.start_of_ship_period or '',
                })
            if record.end_of_ship_period:
                vals.update({
                    'end_of_ship_period': record.end_of_ship_period and record.end_of_ship_period or '',
                })
            if record.end_of_ship_period_actual:
                vals.update({
                    'end_of_ship_period_actual': record.end_of_ship_period_actual or '',
                })
            if record.si_sent_date:
                vals.update({
                    'si_sent_date': record.si_sent_date or '',
                })
            if record.si_received_date:
                vals.update({
                    'si_received_date': record.si_received_date or '',
                })
            if record.pss_send_schedule:
                vals.update({
                    'pss_send_schedule': record.pss_send_schedule or '',
                })
            if record.pss_approved_date:
                vals.update({
                    'pss_approved_date': record.pss_approved_date or '',
                })
            if record.factory_etd:
                vals.update({
                    'factory_etd': record.factory_etd or '',
                })
            if record.nominated_etd:
                vals.update({
                    'nominated_etd': record.nominated_etd or '',
                })
            if record.bill_date:
                vals.update({
                    'bill_date': record.bill_date or '',
                })
            if record.pss_sent_date:
                vals.update({
                    'pss_sent_date': record.pss_sent_date or '',
                })
            if record.eta:
                vals.update({
                    'eta': record.eta or '',
                })
            if record.late_ship_end:
                vals.update({
                    'late_ship_end': record.late_ship_end or '',
                })
            if record.late_ship_est:
                vals.update({
                    'late_ship_est': record.late_ship_est or '',
                })
            if record.pss_late_ontime:
                vals.update({
                    'pss_late_ontime': record.pss_late_ontime or '',
                })
            if record.od_doc_rec_date:
                vals.update({
                    'od_doc_rec_date': record.od_doc_rec_date or '',
                })
            if record.od_doc_sent_date:
                vals.update({
                    'od_doc_sent_date': record.od_doc_sent_date or '',
                })

            s_id = s_contract_obj.create(vals)
            for pssl in record.pss_sent_ids:
                pssl.write({'s_contract_id': s_id.id})


            s_contractl_obj.create({
                'product_id': record.standard_id and record.standard_id.id or 0,
                'certificate_id': record.certificate_id and record.certificate_id.id or 0,
                'name': record.p_quality and record.p_quality or '',
                'packing_id': record.packing_id and record.packing_id.id or 0,
                'product_qty': record.p_qty and record.p_qty or 0,
                'number_of_bags': record.no_of_pack and record.no_of_pack or 0,
                'product_uom': record.standard_id and record.standard_id.uom_id.id or 0,
                'contract_id': s_id.id
            })

            for ship in s_id.shipping_ids:
                ship.button_load_sc()
            record.write({
                'state': 'linked'
            })
            # except:
            #     raise UserError('Can not sync this!!!!')
        return 1

class PssSent(models.Model):
    _inherit = 'pss.sent'

    t_contract_id = fields.Many2one('traffic.contract', string='S Contract')
    x_sequence = fields.Integer('Sequence')

    