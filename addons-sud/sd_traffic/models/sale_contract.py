# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta


class SaleContract(models.Model):
    _inherit = "sale.contract"

    x_p_allocate = fields.Char(string='P Contract', compute='_compute_p_contract', store=True)
    total_allocate_qty = fields.Float(string='Allocate Qty', compute='_compute_allocate_qty', store=True)
    pss_approved = fields.Float(string='PSS Approved')
    pss_count_sent = fields.Float(string='PSS Sent')

    pss_type = fields.Selection(related='scontract_id.traffic_link_id.pss_type', string='Pss Type', store=True)
    pss_reject = fields.Float(string='PSS Reject')
    
    # @api.model
    # def create(self, vals):
    #     new_id = super(SaleContract, self).create(vals)
    #     if 'scontract_id' in vals and vals['scontract_id']:
    #         new_id._compute_pss_approved()
    #     return new_id
    #
    #
    # def write(self, vals):
    #     write_new_id = super(SaleContract, self).write(vals)
    #     if 'scontract_id' in vals and vals['scontract_id']:
    #         self._compute_pss_approved()
    #     return write_new_id
    #
    #
    # def _compute_pss_approved(self):
    #     for record in self:
    #         if record.x_is_bonded != True:
    #             return
    #
    #         record.pss_approved = 0
    #         traffic_contract = record.scontract_id.traffic_link_id and record.scontract_id.traffic_link_id.id or False
    #         if traffic_contract:
    #             update_sp = self.env['fob.pss.management'].search([
    #                 ('x_traffic_contract', '=', record.scontract_id.traffic_link_id.id),
    #                 ('pss_status', '=', 'approved')
    #             ])
    #             record.pss_approved = len(update_sp)
    #             update_sp = self.env['fob.pss.management'].search([
    #                 ('x_traffic_contract', '=', record.scontract_id.traffic_link_id.id),
    #                 ('pss_status', '=', 'sent')
    #             ])
    #             record.pss_count_sent = len(update_sp)

    @api.depends('detail_ids', 'detail_ids.tobe_qty')
    def _compute_allocate_qty(self):
        for record in self:
            record.total_allocate_qty = sum(i.tobe_qty for i in record.detail_ids)
    
    



    @api.depends('detail_ids', 'detail_ids.p_contract_id')
    def _compute_p_contract(self):
        for record in self:
            try:
                record['x_p_allocate'] = ', '.join([x.p_contract_id.name for x in record.detail_ids if record.detail_ids])
            except:
                record['x_p_allocate'] = ''

    def button_cancel(self):
        for record in self:
            if record.detail_ids:
                raise UserError(_("You have allocated P contract in S-P Allocation, "
                                  "please delete all allocated first and try again!!!!"))
            record.write({'state': 'cancel'})


class SaleContractDeatail(models.Model):
    _inherit = 'sale.contract.deatail'

    code_stack = fields.Char(string='WR No', related='stack_id.code', store=True)

    def button_set_to_draft(self):
        for record in self:
            record.write({
                'state': 'draft'
            })
