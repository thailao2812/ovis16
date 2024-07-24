# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models
from datetime import datetime
from pytz import timezone

import logging
_logger = logging.getLogger(__name__)

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
NAME_DATETIME_FORMAT = "%Y%m%d.%H%M"


class SynchronizeDataConfigLine(models.Model):
    _name = 'api.synchronize.data.config.line'
    _description = 'API Synchronize Data Config Line'

    config_id = fields.Many2one(
        'api.synchronize.data.config',
        'Config',
    )
    fields_id = fields.Many2one(
        'ir.model.fields',
        string="Fields",
        required=True,
        ondelete='cascade',
    )

    fields_name = fields.Char(
        related='fields_id.name',
        string="Fields Name",
        store=True,
    )
    ttype = fields.Selection(
        related='fields_id.ttype',
        string='Field Type',
        store=True
    )

    fields_sys = fields.Char(
        string='Fields Syn',
        required=True,
    )
    model_sys = fields.Char(
        string='Model Syn',
    )
    value_sys = fields.Char(
        string='Value Syn',
    )

    relation = fields.Char(
        related='fields_id.relation',
        string='Object Relation',
        store=True
    )

    config_sys_id = fields.Many2one(
        'api.synchronize.data.config',
        string="Config Syn",
    )

    is_sync = fields.Boolean(
        string="Synchronized",
        store=True
    )

    def _onchange_fields_id(self):
        for rec in self:
            if rec.fields_id and rec.fields_id.relation:
                model_fields = self.env[rec.fields_id.relation]._fields
                rec.write({
                    'is_sync': 'sync_id' in model_fields and True or False
                })
