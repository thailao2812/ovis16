# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class NedCertificateLicense(models.Model):
    _inherit = "ned.certificate.license"

    estate_name = fields.Char(string='Estate Name', related='partner_id.estate_name', store=True)