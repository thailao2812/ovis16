# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

DATE_FORMAT = "%Y-%m-%d"
import time
import datetime
from datetime import date
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class NedCertificateLicense(models.Model):
    _inherit = 'ned.certificate.license'

    # FAQ Derivable
    g3_derivable = fields.Float(string='G3 Derivable', compute='_compute_total_allocated_amount', store=True)
    g3_allocated = fields.Float(string='G3 Allocated', compute='_compute_total_allocated_amount', store=True)
    g3_allocated_not_out = fields.Float(string='G3 Tobe Ship',
                                        compute='_compute_total_allocated_amount', store=True)
    g3_allocated_out = fields.Float(string='G3 Shipped',
                                    compute='_compute_total_allocated_amount', store=True)
    g3_unallocated = fields.Float(string='G3 Un Allocate', compute='_compute_total_allocated_amount', store=True)
    g3_balance = fields.Float(string='G3 Balance', compute='_compute_total_allocated_amount', store=True)
    g3_position = fields.Float(string='G3 Position', compute='_compute_total_allocated_amount', store=True)

    total_position = fields.Float(string='Total Position', compute='_compute_total_allocated_amount', store=True )
    state_id = fields.Many2one('res.country.state', string='Province')

    state = fields.Selection(
        [('draft', 'Draft'),
         ('approve', 'Approve'),
         ('active', 'Active'),
         ('expired', 'Expired'),
         ('deactive', 'Deactive'),
         ('transfered', 'Transfered')],
        string="Status", default='draft')

    edur_compliant = fields.Char(string='EUDR Compliant')
    eudr_check = fields.Boolean(string='Is EUDR', default=False)
    combine_check = fields.Boolean(string='Is Combined', default=False)
    cert_combine = fields.Many2many('ned.certificate', 'ned_certificate_license_ned_certificate_rel', 'license_number_id', 'certificate_id', string="Cer Combine",) 
                            # readonly=True)
                            # readonly=True, states={'draft': [('readonly', False)],'sec_confirm': [('readonly', False)]})

    @api.onchange("eudr_check", "combine_check", 'certificate_id')
    def onchange_cert_combine(self):
        if self.certificate_id:
            cer_arr = []
            if self.eudr_check:
                if self.combine_check:
                    cer_list = self.env['ned.certificate'].search(['|', '|', ('name','=',self.certificate_id.name),('name','=','EUDR'),('name','=like',self.certificate_id.name + '-%')])
                    self.cert_combine = cer_list
                else:
                    cer_list = self.env['ned.certificate'].search(['|', ('name','=',self.certificate_id.name),('name','=','EUDR')])
                    for cer in cer_list:
                        cer_arr.append(cer.id)
                self.cert_combine = cer_arr
            else:
                self.combine_check = False
                self.cert_combine = self.certificate_id

    def button_approve(self):
        for rec in self:
            rec.state ='approve'

    @api.depends('shipping_instruction_allocation_ids.allocation_qty', 'shipping_instruction_allocation_ids',
                 'sales_allocation_ids', 'sales_allocation_ids.allocation_qty',
                 'shipping_instruction_allocation_ids.state', 'g1_s16_initial', 'g1_s18_initial', 'g2_initial')
    def _compute_total_allocated_amount(self):
        res = super(NedCertificateLicense, self)._compute_total_allocated_amount()
        for record in self:
            record.g3_derivable = 0

            record.g3_allocated = sum(record.shipping_instruction_allocation_ids.filtered(
                    lambda x: x.grade_id.code == 'G3').mapped('allocation_qty'))
            record.g3_allocated_out = sum(record.shipping_instruction_allocation_ids.filtered(
                    lambda x: x.grade_id.code == 'G3' and x.state == 'done').mapped('allocation_qty'))
            if record.sales_allocation_ids:
                record.g3_allocated_out += sum(record.sales_allocation_ids.filtered(
                    lambda x: x.grade_id.code == 'G3').mapped('allocation_qty'))

            record.g3_allocated_not_out = record.g3_allocated - record.g3_allocated_out
            record.g3_unallocated = record.g3_derivable - record.g3_allocated
            record.g3_balance = record.g3_derivable - record.g3_allocated_out
            record.final_balance = record.faq_balance + record.g1_s18_balance + record.g1_s16_balance \
                                   + record.g2_balance + record.g3_balance

            record.g3_position = record.g3_balance

            record.total_position = record.faq_position + record.g1_s18_position + record.g1_s16_position + record.g2_position + record.g3_position

        return res

