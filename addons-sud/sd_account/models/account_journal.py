# -*- coding: utf-8 -*-
from odoo import api, Command, fields, models, _
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from odoo.addons.base.models.res_bank import sanitize_account_number
from odoo.tools import remove_accents
import logging
import re

class AccountJournal(models.Model):
    _inherit = "account.journal"
    
    
    # THANH 080123 - sử dụng field sequence để sinh số phiếu hạch toán (thay thế cách sinh mã của Odoo 14)
    sequence_id = fields.Many2one('ir.sequence', string='Entry Sequence',
                                  help="This field contains the information related to the numbering of the journal entries of this journal.",
                                  required=False, copy=False)
    
    
    trans_type = fields.Selection([('local', 'Local'), ('export', 'Export')], string='Trans Type', default='export') 



    @api.constrains('type', 'default_account_id')
    def _check_type_default_account_id_type(self):
        for journal in self:
            #Kiệt 
            return
            if journal.type in ('sale', 'purchase') and journal.default_account_id.account_type in ('asset_receivable', 'liability_payable'):
                raise ValidationError(_("The type of the journal's default credit/debit account shouldn't be 'receivable' or 'payable'."))