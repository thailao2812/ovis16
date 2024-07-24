# -*- coding: utf-8 -*-
import math

from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import UserError
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
import time
from datetime import datetime,date, timedelta


class PostShipmentLine(models.Model):
    _inherit = "post.shipment.line"

    net_qty = fields.Float(string="Net Qty (In Kgs)")
    seal_number = fields.Char(string='Seal Number')
    do_id = fields.Many2one('delivery.order', related=False,  string='DO Number',store=True)
    do_date = fields.Date(related='do_id.date', string='DO Date', store=True)
    cont_no = fields.Char(string='Cont no.', size=128, required=False)