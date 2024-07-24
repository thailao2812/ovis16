# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict

from docutils.nodes import document
import calendar
import datetime
from time import gmtime, strftime
DATE_FORMAT = "%Y-%m-%d"

class FOB_Deviation(models.Model):
    _name = 'v.fob.deviation'
    _description = 'FOB Deviation Report'
    _auto = False

    do_no = fields.Char(sring = 'DO No.')
    fob_date = fields.Date(string = 'DO Date')
    si_no = fields.Char(sring = 'SI No.')
    con_name = fields.Char(string = 'NVS-NLS')
    product = fields.Char(string = 'Product')
    total_qty = fields.Float(string = 'Qty (Kg)', digits=(12, 0))
    trucking_no = fields.Char(string = 'Trucking No.')
    placename = fields.Char(string = 'Delivery Place')
    pickingname = fields.Char(string = 'GDN No.')
    state = fields.Char(string = 'Status')
    transrate = fields.Float(string = 'Trans. Rate (VNĐ)', digits=(12, 0))
    bagsfactory = fields.Float(string = 'Bags Factory', digits=(12, 0))
    bagshcm = fields.Float(string = 'Bags HCM', digits=(12, 0))
    weightfactory = fields.Float(string = 'Weight Factory (Kg)', digits=(12, 0))
    shipped_weight = fields.Float(string = 'Weight HCM (Kg)', digits=(12, 0))
    storing_loss = fields.Float(string = 'Storing Loss (Kg)', digits=(12, 0))
    transportation_loss = fields.Float(string = 'Trans. Loss (Kg)', digits=(12, 0))

    @api.depends('transportation_loss', 'weightfactory', 'shipped_weight', 'storing_loss')
    def _trans_loss_rate(self):
        for record in self:
            if record.transportation_loss > 0 and record.weightfactory > 0 and record.shipped_weight > 0:
                record.trans_loss_per = record.transportation_loss / record.weightfactory * 100
                record.store_loss_per = record.storing_loss / record.shipped_weight * 100
                if record.transportation_loss / record.weightfactory * 100 > 0.1:
                    record.claim_percent = record.transportation_loss - (record.weightfactory * 0.1 / 100)
                else:
                    record.claim_percent = 0
            else:
                # record.trans_loss_rate = 0
                # record.store_loss_rate = 0
                record.trans_loss_per =0
                record.store_loss_per =0
                record.claim_percent =0

    trans_loss_per = fields.Float(compute='_trans_loss_rate', digits=(12, 2) , string='Trans. Loss %')
    store_loss_per = fields.Float(compute='_trans_loss_rate', digits=(12, 2) , string='Storing Loss %')
    claim_percent = fields.Float(compute='_trans_loss_rate', digits=(12, 0) , string='Claim (>0.1%) (kg)')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'v_fob_deviation')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW public.v_fob_deviation AS
             SELECT row_number() OVER (ORDER BY deli.name DESC) AS id,
                deli.name AS do_no,
                deli.date AS fob_date,
                ins.name AS si_no,
                scon.name AS con_name,
                pro.default_code AS product,
                deli.total_qty,
                deli.trucking_no,
                ins.placename,
                spick.name AS pickingname,
                deli.state,
                deli.transrate,
                deli.bagsfactory,
                deli.bags AS bagshcm,
                deli.weightfactory,
                deli.shipped_weight,
                deli.total_qty - deli.weightfactory AS storing_loss,
                deli.transportation_loss
               FROM delivery_order deli
                 JOIN ( SELECT a.id,
                        a.origin,
                        a.create_date,
                        a.sequence,
                        a.container_status,
                        a.write_uid,
                        --a.final_destination,
                        a.ico_permit_no,
                        a.partner_id,
                        a.create_uid,
                        a.booking_date,
                        a.contract_id,
                        --a.shipment_from,
                        --a.message_last_post,
                        a.company_id,
                        --a.forwarding_agent_moved0,
                        a.note,
                        a.state,
                        --a.delivery_to,
                        --a.type,
                        a.vessel_flight_no,
                        a.ico_permit_date,
                        a.warehouse_id,
                        a.reach_date,
                        a.write_date,
                        a.date,
                        --a.delivery_from,
                        a.user_approve,
                        a.date_approve,
                        --a.port_of_discharge_moved0,
                        a.transaction,
                        a.name,
                        --a.shipping_line_moved0,
                        --a.port_of_loading_moved0,
                        a.eta,
                        --a.etd,
                        a.booking_ref_no,
                        a.port_of_discharge,
                        a.shipping_line,
                        a.port_of_loading,
                        a.deadline,
                        a.marking,
                        a.user_confirm,
                        a.type_of_stuffing,
                        a.date_confirm,
                        --a.prodcompleted_moved0,
                        a.materialstatus,
                        a.shipment_date,
                        --a."Fumigation_date",
                        a.fumigation_id,
                        --a.pss_send,
                        a.pss_approved,
                        a.shipped,
                        a.fumigation_date,
                        a.factory_etd,
                        a.push_off_etd,
                        a.closing_time,
                        a.forwarding_agent,
                        a.pss_sent,
                        a.shipping_line_id,
                        a.incoterms_id,
                        a.date_sent,
                        a.delivery_place_id,
                        a.pss_condition,
                        a.bill_no,
                        a.bill_date,
                        a.vessel,
                        a.voyage,
                        --a.qty_mrp,
                        a.prodcompleted,
                        a.remarks,
                        a.priority_by_month,
                        a.pss_send_schedule,
                        --a.completed_date,
                        a.production_status,
                        a.status,
                        b.name AS placename
                       FROM shipping_instruction a
                         JOIN delivery_place b ON a.delivery_place_id = b.id) ins ON deli.shipping_id = ins.id
                 JOIN sale_contract scon ON deli.contract_id = scon.id
                 JOIN product_product pro ON deli.product_id = pro.id
                 JOIN stock_picking spick ON deli.picking_id = spick.id;
            """)

