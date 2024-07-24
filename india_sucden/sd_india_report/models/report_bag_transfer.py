# -*- coding: utf-8 -*-
from odoo import api
from odoo import SUPERUSER_ID
from odoo import tools
from odoo import fields, models
from odoo.tools.translate import _
from odoo.exceptions import UserError
from datetime import datetime, timedelta, date
import time
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
from docutils.nodes import document
import calendar
import datetime
from time import gmtime, strftime
DATE_FORMAT = "%Y-%m-%d"


class ReportBagTransfer(models.Model):
    _name = 'report.bag.transfer'
    _description = 'Report Bag Transfer'

    partner_id = fields.Many2one('res.partner', string='Supplier')
    product_id = fields.Many2one('product.product', string='Name of Bag')
    bag_in = fields.Float(string='No of Bag In')
    bag_out = fields.Float(string='No of bag Out')
    balance = fields.Float(string='Balance', compute='compute_balance', store=True)

    @api.depends('bag_in', 'bag_out')
    def compute_balance(self):
        for record in self:
            record.balance = record.bag_in - record.bag_out