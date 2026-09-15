# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError


class SContract(models.Model):
    _inherit = 's.contract'

    pss_type = fields.Selection(
        [('SAS', 'SAS'), ('SAN', 'SAN'), ('SAP', 'SAP'), ('PSS', 'PSS'), ('PSS+OTS', 'PSS+OTS'), ('No', 'Non PSS')],
        string=" Pss type", copy=True)