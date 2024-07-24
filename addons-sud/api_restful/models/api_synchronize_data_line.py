# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models
from datetime import datetime
from pytz import timezone

import logging
_logger = logging.getLogger(__name__)

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
NAME_DATETIME_FORMAT = "%Y%m%d.%H%M"


class SynchronizeDataLine(models.Model):
    _name = 'api.synchronize.data.line'
    _description = 'API Synchronize Data Line'
    _order = "id desc"

    synchronize_id = fields.Many2one(
        'api.synchronize.data',
        'synchronize',
    )

    slc_method = fields.Selection(
        [
            ('get', "Search"),
            ('post', 'Create'),
            ('put', 'Write'),
            ('patch', 'Action'),
            ('delete', 'Delete'),
        ],
        string="Method"
    )
    payload = fields.Text(
        string="Payload"
    )

    result = fields.Html(
        string='Result'
    )

    state = fields.Selection(
        [
            ('done', "Done"),
            ('failed', 'Failed'),
            ('waiting', 'Waiting'),
        ],
        default='waiting',
        string="Status"
    )
