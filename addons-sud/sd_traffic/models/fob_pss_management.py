# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta


class FOBPssManagement(models.Model):
    _inherit = "fob.pss.management"

    @api.model
    def create(self, vals):
        new_id = super(FOBPssManagement, self).create(vals)
        if 'x_traffic_contract' in vals and vals['x_traffic_contract']:
            new_id._compute_pss_approved()
        return new_id

    def write(self, vals):
        write_new_id = super(FOBPssManagement, self).write(vals)
        if self.x_traffic_contract:
            self._compute_pss_approved()
        return write_new_id

    def _compute_pss_approved(self):
        for record in self:
            sale_contract = False
            if record.x_traffic_contract:
                sale_contract = self.env['sale.contract'].search([
                    ('scontract_id.traffic_link_id', '=', record.x_traffic_contract.id),
                    ('state', '!=', 'cancel')
                ])
            if not sale_contract:
                return
            if sale_contract.x_is_bonded != True:
                return

            # record.pss_approved = 0
            traffic_contract = record.x_traffic_contract and record.x_traffic_contract.id or False
            if traffic_contract:
                update_sp = self.env['fob.pss.management'].search([
                    ('x_traffic_contract', '=', traffic_contract),
                    ('pss_status', '=', 'approved')
                ])
                sale_contract.pss_approved = len(update_sp)
                update_sp_1 = self.env['fob.pss.management'].search([
                    ('x_traffic_contract', '=', traffic_contract),
                    ('pss_status', '=', 'sent')
                ])
                sale_contract.pss_count_sent = len(update_sp_1)
