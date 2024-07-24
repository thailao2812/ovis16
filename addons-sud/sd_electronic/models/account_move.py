


# -*- encoding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.addons.report_aeroo.report_parser import Parser

import datetime
import time
import pytz
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

import requests
import json
import base64

class AccountMove(models.Model):
    _inherit = 'account.move'

    ref_id = fields.Char('RefID', readonly=True)
    origin = fields.Char('Number')
    transaction_id = fields.Char('TransactionID', readonly=True)
    invoice_number = fields.Char('Invoice Number', readonly=True)
    invoice_issue_date = fields.Date('Invoice Issued Date', readonly=True)
    status = fields.Char(string="Status", readonly=True, required=False, )
    base64_pdf = fields.Char(string="PDF", required=False, )
    ref_type = fields.Char('RefType', readonly=True)

    org_ref_id = fields.Char('RefID', readonly=True)
    org_invoice_number = fields.Char('Org Invoice Number', readonly=True)
    org_invoice_issued_date = fields.Date('Org Invoice Issued Date',
                                          readonly=True)
    type_invoice = fields.Selection(string="Is Invoice",
                                    selection=[('is_invoice_instead',
                                                'Is Invoice Instead ?'), (
                                                   'is_invoice_adjustment',
                                                   'Is Invoice Adjustment ?'),
                                               ], readonly=True)
    
    reference_description = fields.Char('Reference/Description')

    
    def print_preview_invoice(self):
        return

    def e_invoicing(self):
        return
    
    def convert_invoice(self):
        return