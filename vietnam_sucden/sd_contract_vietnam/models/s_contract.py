# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class SContract(models.Model):
    _inherit = 's.contract'

    pss_type = fields.Selection(
        [('SAS', 'SAS'), ('SAN', 'SAN'), ('SAP', 'SAP'), ('PSS', 'PSS'),('SOD', 'SOD'), ('PSS+OTS', 'PSS+OTS'), ('No', 'No')],
        string=" Pss type", copy=True)