# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models
from datetime import datetime
from pytz import timezone

import logging
_logger = logging.getLogger(__name__)

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
NAME_DATETIME_FORMAT = "%Y%m%d.%H%M"


class SynchronizeDomainConfig(models.Model):
    _name = 'api.synchronize.domain.config'
    _description = 'API Synchronize Domain Config'
    _rec_name = 'new_model'
    _sql_constraints = [('name_model',
                         'unique(new_model)',
                         "Synchronize Domain already exists !")]

    new_model = fields.Char(
        string="Model Synchronize v14",
        required=True,
    )

    domain = fields.Text(
        string="Domain Synchronize v14",
        required=True,
    )


class SynchronizeDataConfig(models.Model):
    _name = 'api.synchronize.data.config'
    _description = 'API Synchronize Data Config'

    model = fields.Char(
        string="Model",
        required=True,
    )

    new_model = fields.Char(
        string="Model Synchronize v14",
        required=True,
    )

    state = fields.Selection(
        [
            ('draft', "Draft"),
            ('post', 'Post'),
        ],
        default="draft",
        string="Status",
    )

    line_ids = fields.One2many(
        'api.synchronize.data.config.line',
        'config_id',
        'synchronize data line',
    )

    is_change = fields.Boolean(
        string="Has changed"
    )


    _sql_constraints = [
        ('name_model', 'unique (model)', "Tag model already exists !"),
    ]

    def action_post(self):
        for rcs in self:
            rcs.reset_data_done()
            rcs.line_ids._onchange_fields_id()
            model_api_id = self.env['ir.model'].search([
                ('model', '=', rcs.model)
            ])
            if model_api_id:
                model_api_id.write({
                    'restful_api': True
                })
            rcs.write({
                'is_change': False,
                'state': 'post'
            })

    def action_draft(self):
        for rcs in self:
            rcs.line_ids._onchange_fields_id()
            rcs.write({
                'is_change': False,
                'state': 'draft'
            })
            model_api_id = self.env['ir.model'].search([
                ('model', '=', rcs.model)
            ])
            if model_api_id:
                model_api_id.write({
                    'restful_api': False
                })

    @api.depends('model')
    def name_get(self):
        result = []
        for rcs in self:
            name = rcs.model
            result.append((rcs.id, name))
        return result

    @api.onchange('line_ids')
    def onchange_line_ids(self):
        for rec in self:
            rec.is_change = True

    def reset_data_done(self):
        if not self.is_change:
            return
        done_record_ids = self.env['api.synchronize.data'].search(
            [('model', '=', self.model), ('state', '=', 'done')]).filtered(lambda x: x.reference)
        for record in done_record_ids:
            if record.slc_method == 'put':
                record.state = 'waiting'
            else:
                record.slc_method = 'put'
                record.state = 'waiting'
            record_id = self.env[self.model].browse(record.res_id)
            record.line_ids = [(0, 0, {
                'state': 'waiting',
                'slc_method': 'put',
                'payload': record.prepare_payload(record_id, self)
            })]
