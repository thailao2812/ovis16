# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class SContractLicenseAllocation(models.Model):
    _inherit = 's.contract.license.allocation'
    

    type = fields.Selection(related='license_id.type', string='Type', store=True)
    

