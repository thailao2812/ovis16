# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
from lxml import etree
import base64
import xlrd
import math



class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        context = self._context or {}
        #THANH: Filter payment methods for menu Sales / Deposit and Remaining Payments
        if context.get('filter_by_company'):
            args += [('is_company', '=', True)]
        return super(ResPartner, self).search(args, offset, limit, order, count=count)
    
    
    
    
