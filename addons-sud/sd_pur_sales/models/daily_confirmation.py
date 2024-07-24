import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
import xlrd
import base64
from xlrd import open_workbook



class DailyConfirmationLine(models.Model):
    _inherit ='daily.confirmation.line'

    contract_id = fields.Many2one('purchase.contract', string='Contract No.')

    
    