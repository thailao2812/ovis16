# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError


class TrafficContractFilter(models.Model):
    _name = "traffic.contract.filter"

    name = fields.Char('Name', size=256)
    date_from = fields.Date('From')
    date_to = fields.Date('To')
    origin_ids = fields.Many2many('res.country', 'filter_origin_rel', 'filter_id', 'origin_id', 'Origin')

    def open_scontract(self):
        period_obj = self.env['s.period']
        period_ids = []
        origin_ids = []
        for x in self:
            if x.date_from:
                period_ids = period_obj.search([('date_from', '>=', x.date_from)])
                if x.date_to:
                    period_ids = period_obj.search([
                        ('date_from', '>=', x.date_from),
                        ('date_to', '<=', x.date_to)
                    ])
            if period_ids:
                period_ids = [i.id for i in period_ids]
            if x.origin_ids:
                origin_ids = [ii.id for ii in x.origin_ids]
        form_view_id = self.env.ref('sd_traffic.view_traffic_contract_filter_tree')

        return {
            'name': 'S Contract',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'traffic.contract',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'views': [(form_view_id.id, 'tree')],
            'domain': "[('shipt_month', 'in', %s), ('origin_new', 'in', %s)]" % (str(period_ids), str(origin_ids))
        }